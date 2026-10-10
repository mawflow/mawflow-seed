import importlib.util
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

SCRIPTS = Path(__file__).resolve().parents[1] / "ops/scripts"
sys.path.insert(0, str(SCRIPTS))
from update_notes.render import cloud_documents, import_changelogs, render  # noqa: E402
from update_notes.store import CLOUD, HISTORY, LATEST, load_notes, validate, write_bytes  # noqa: E402

SPEC = importlib.util.spec_from_file_location(
    "generate_update_notes", SCRIPTS / "generate-update-notes.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.fixture
def root(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/evidence.md").write_text("已执行验证\n")
    (tmp_path / ".maw/changes").mkdir(parents=True)
    return tmp_path


def note(key="update.001", *, occurred_at="2026-10-04T12:00:00+08:00", **kwargs):
    payload = {
        "schema": "mawflow.update_note.v1",
        "occurred_at": occurred_at,
        "title": "生成更新动态",
        "summary": "支持最近100条及完整历史",
        "category": "added",
        "module_key": "governance",
        "module_name": "项目治理",
        "importance": "normal",
        "audience": "project",
        "delivery_state": "implemented",
        "validation_state": "unverified",
        "details": [{"label": "详情", "path": "docs/evidence.md"}],
    }
    payload.update(kwargs)
    return {
        "schema_version": 1,
        "record_key": key,
        "task_key": "test-update-notes",
        "record_type": "update_note",
        "operation": "append",
        "payload": payload,
        "evidence_refs": [{"path": "docs/evidence.md", "kind": "test_result"}],
    }


def store(root, value, filename=None):
    path = root / ".maw/changes" / (filename or value["record_key"] + ".yaml")
    path.write_text(yaml.safe_dump(value, allow_unicode=True))


def run(root, *options):
    return MODULE.run(MODULE.parser().parse_args([*options, "--root", str(root)]))


def apply(root, *options):
    preview = run(root, *options)
    return run(
        root, *options, "--execute", "--expected-fingerprint", preview["fingerprint"]
    )


def test_default_hundred_all_and_stable_repeat(root):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for index in range(105):
        store(
            root,
            note(
                f"update.{index:03}",
                occurred_at=(start + timedelta(hours=index)).isoformat(),
            ),
        )
    preview = run(root, "render")
    assert preview["selected"] == 100
    assert not (root / LATEST).exists()
    first = apply(root, "render")
    latest = (root / LATEST).read_bytes()
    assert latest.count(b"<!-- update.") == 100
    assert b"<!-- update.000 -->" not in latest
    assert first["changed_paths"] == [LATEST]
    assert apply(root, "render")["changed_paths"] == []
    apply(root, "render", "--all")
    assert (root / HISTORY).read_bytes().count(b"<!-- update.") == 105
    assert (root / LATEST).read_bytes() == latest
    apply(root, "render-cloud")
    assert run(root, "check")["status"] == "success"


def test_sort_uses_actual_timezone_and_identity_tie_break(root):
    store(root, note("update.a", occurred_at="2026-10-04T12:00:00+08:00"))
    store(root, note("update.b", occurred_at="2026-10-04T05:00:00+00:00"))
    store(root, note("update.c", occurred_at="2026-10-04T13:00:00+08:00"))
    assert [item["record_key"] for item in load_notes(root)[0]] == [
        "update.c",
        "update.b",
        "update.a",
    ]


def test_record_is_immutable_idempotent_and_stale_preview_stops(root):
    source = root / "input.json"
    source.write_text(json.dumps(note()))
    apply(root, "record", "--input", str(source))
    assert apply(root, "record", "--input", str(source))["changed_paths"] == []
    source.write_text(json.dumps(note(summary="不同内容")))
    with pytest.raises(ValueError, match="immutable_record_conflict"):
        run(root, "record", "--input", str(source))
    preview = run(root, "render")
    store(root, note("update.other"))
    with pytest.raises(ValueError, match="stale_or_missing"):
        run(
            root,
            "render",
            "--execute",
            "--expected-fingerprint",
            preview["fingerprint"],
        )
    assert not (root / LATEST).exists()


def test_duplicate_conflict_and_other_fragment_compatibility(root):
    store(root, note())
    store(root, note(), "duplicate.yaml")
    store(
        root,
        {"schema_version": 1, "record_type": "capability", "payload": {}},
        "capability.yaml",
    )
    assert len(load_notes(root)[0]) == 1
    store(root, note(summary="并行冲突"), "duplicate.yaml")
    with pytest.raises(ValueError, match="conflicting_record_identity"):
        load_notes(root)


def test_corrections_preserve_history_and_parallel_forks_fail(root):
    store(root, note())
    store(
        root,
        note(
            "update.002",
            occurred_at="2026-10-05T12:00:00+08:00",
            supersedes="update.001",
        ),
    )
    apply(root, "render", "--all")
    output = (root / HISTORY).read_text()
    assert "已更正" in output and output.count("<!-- update.") == 2
    store(
        root,
        note(
            "update.003",
            occurred_at="2026-10-06T12:00:00+08:00",
            supersedes="update.001",
        ),
    )
    with pytest.raises(ValueError, match="conflicting_revision"):
        load_notes(root)


@pytest.mark.parametrize(
    "patch,error",
    [
        ({"occurred_at": "2026-10-04T12:00:00"}, "timezone"),
        ({"category": "invented"}, "invalid_category"),
        ({"delivery_state": "planned"}, "invalid_delivery_state"),
        ({"delivery_state": "released"}, "release_evidence"),
        ({"validation_state": "human_accepted"}, "human_acceptance_evidence"),
        ({"summary": "pass" "word=abcdefghijk"}, "sensitive"),
        ({"summary": "本机 /" "home/alice/private"}, "sensitive"),
        (
            {"details": [{"label": "私有", "path": ".local/passwords.md"}]},
            "private_path",
        ),
        ({"details": [{"label": "逃逸", "path": "../outside.md"}]}, "unsafe_relative"),
        (
            {"details": [{"label": "私有", "path": "docs/archive/history.md"}]},
            "private_path",
        ),
        (
            {
                "details": [
                    {"label": "链接", "url": "https://example.test/doc?token=hidden"}
                ]
            },
            "unsafe_detail",
        ),
        (
            {"details": [{"label": "链接", "url": "javascript:alert(1)"}]},
            "unsafe_detail",
        ),
    ],
)
def test_rejected_input_is_not_written(root, patch, error):
    with pytest.raises(ValueError, match=error):
        validate(root, note(**patch))


def test_symlink_and_output_escape_are_rejected(root, tmp_path):
    (root / "docs/link.md").symlink_to(root / "docs/evidence.md")
    with pytest.raises(ValueError, match="symlink"):
        validate(root, note(details=[{"label": "详情", "path": "docs/link.md"}]))
    with pytest.raises(ValueError, match="output_outside"):
        run(root, "render", "--output", "docs/evidence.md")
    with pytest.raises(ValueError, match="unsafe_relative"):
        run(root, "render", "--output", "docs/updates/../../outside.md")


def test_atomic_concurrent_append(root):
    content = b"complete immutable record\n"
    path = ".maw/changes/concurrent.yaml"
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(
            pool.map(lambda _: write_bytes(root, path, content, append=True), range(4))
        )
    assert sum(results) == 1
    assert (root / path).read_bytes() == content
    with pytest.raises(ValueError, match="immutable"):
        write_bytes(root, path, b"changed", append=True)


def changelog(root, *rows):
    source = "docs/changelogs/governance.md"
    (root / source).parent.mkdir(exist_ok=True)
    (root / source).write_text("\n".join(rows) + "\n")
    return source


def test_explicit_import_retries_do_not_reclassify_history_or_duplicate(root):
    row = "| 2026-09-01 | pending | 历史任务 | feature/fix | 原始变更摘要 | confirmed | 未发布 |"
    source = changelog(root, row)
    apply(root, "import-changelogs", "--source", source)
    first = load_notes(root)[0][0]
    assert first["payload"]["delivery_state"] == "historical"
    assert first["payload"]["validation_state"] == "unverified"
    changelog(
        root, row, "| 2026-09-02 | v1 | 新任务 | docs | 新摘要 | confirmed | docs |"
    )
    assert (
        apply(root, "import-changelogs", "--source", source)["imported_or_recorded"]
        == 1
    )
    assert len(load_notes(root)[0]) == 2
    assert apply(root, "import-changelogs", "--source", source)["changed_paths"] == []


def test_import_rejects_private_rows_with_visible_warning(root):
    source = changelog(
        root,
        "| 2026-09-01 | pending | 私有 | fix | /" "home/alice/private | confirmed | 未发布 |",
    )
    notes, warnings = import_changelogs(root, [source])
    assert notes == [] and "import_row_rejected" in warnings[0]
    with pytest.raises(ValueError, match="explicit_import"):
        run(root, "import-changelogs")


def test_import_preserves_pipes_inside_inline_code(root):
    source = changelog(
        root,
        "| 2026-09-01 | pending | 任务 | fix | 修复 `a | b` 与 `x || y` | confirmed | 来源 |",
    )
    notes, warnings = import_changelogs(root, [source])
    assert not warnings
    assert notes[0]["payload"]["summary"] == "修复 `a | b` 与 `x || y`"


def test_markdown_links_are_relative_and_injected_markup_is_escaped(root):
    output = render(
        root,
        [note(summary="<script>alert(1)</script> [fake](javascript:x)")],
        LATEST,
        100,
        "测试项目",
    )
    decoded = output.decode()
    assert "<script>" not in decoded and "&lt;script&gt;" in decoded
    assert "[详情](../evidence.md)" in decoded
    assert "visibility: project_private" in decoded and "enabled: true" in decoded


def test_check_fails_after_source_change_and_empty_projects_are_explicit(root):
    apply(root, "render")
    apply(root, "render", "--all")
    assert "暂无已记录动态" in (root / LATEST).read_text()
    store(root, note())
    with pytest.raises(ValueError, match="generated_document_drift"):
        run(root, "check")


def test_cli_returns_safe_error_without_source_leak(root):
    source = root / "bad.yaml"
    source.write_text("secret: [unterminated-secret-value")
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "generate-update-notes.py"),
            "record",
            "--root",
            str(root),
            "--input",
            str(source),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 20 and result.stderr == ""
    assert "unterminated-secret-value" not in result.stdout
    assert json.loads(result.stdout)["status"] == "failed"


def test_cloud_archives_cover_all_records_without_broken_source_links(root):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    records = [
        note(
            f"update.{index:03}",
            occurred_at=(start + timedelta(hours=index)).isoformat(),
        )
        for index in range(205)
    ]
    records.reverse()
    documents = cloud_documents(root, records, "测试项目")
    pages = [value for path, value in documents.items() if "update-history/" in path]
    assert len(pages) == 3
    assert sum(content.count(b"<!-- update.") for content in pages) == 205
    assert all(len(content) < 512 * 1024 for content in pages)
    assert "来源：`docs/evidence.md`" in documents[CLOUD].decode()
    assert "[详情]" not in documents[CLOUD].decode()
    manifest = json.loads(documents[".maw/generated/update-notes-cloud.json"])
    assert manifest["status"] == "prepared_not_published"
    assert manifest["total"] == 205


def test_source_evidence_change_invalidates_record_preview(root):
    source = root / "input.json"
    source.write_text(json.dumps(note()))
    preview = run(root, "record", "--input", str(source))
    (root / "docs/evidence.md").write_text("变化后的依据")
    with pytest.raises(ValueError, match="stale_or_missing"):
        run(
            root,
            "record",
            "--input",
            str(source),
            "--execute",
            "--expected-fingerprint",
            preview["fingerprint"],
        )
    assert list((root / ".maw/changes").glob("*.yaml")) == []
