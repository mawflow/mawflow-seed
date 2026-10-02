from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from typing import Any


DEFAULT_PACKAGE_INDEX_URL = "https://mawflow.com/packages/simple"
DEFAULT_TEMPLATE_PACKAGE = "mawflow-seed-kit"
DEFAULT_GITHUB_REPO = "https://github.com/mawflow/mawflow-seed.git"
DEFAULT_GITEE_REPO = "https://gitee.com/mawflow/mawflow-seed.git"
PUBLIC_PAYLOAD_MANIFEST = "PUBLIC_PAYLOAD_MANIFEST.json"
SEED_KIT_MANIFEST_SCHEMA = "mawflow.seed_kit.manifest.v2"
PUBLIC_PAYLOAD_SCHEMA = "mawflow.seed_public_payload.v2"
PUBLIC_VERSION_RE = re.compile(r"^v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


class TemplateSourceError(RuntimeError):
    pass


@dataclass
class TemplateSourceConfig:
    source: str = "package"
    index_url: str = DEFAULT_PACKAGE_INDEX_URL
    template: str = DEFAULT_TEMPLATE_PACKAGE
    template_version: str = ""
    repo: str = ""
    ref: str = ""
    path: str = ""
    git_env: dict[str, str] | None = None


@dataclass
class MaterializedTemplate:
    template_dir: Path
    manifest_path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    cleanup: tempfile.TemporaryDirectory[str] | None = None

    def close(self) -> None:
        if self.cleanup is not None:
            self.cleanup.cleanup()
            self.cleanup = None


def package_requirement(package_name: str, version: str = "") -> str:
    if version:
        return f"{package_name}=={version}"
    return package_name


def normalize_git_repo(source: str, repo: str) -> str:
    raw = (repo or "").strip()
    if source == "github" and not raw:
        return DEFAULT_GITHUB_REPO
    if source == "gitee" and not raw:
        return DEFAULT_GITEE_REPO
    if source == "git" and not raw:
        raise TemplateSourceError("--repo is required when --source git is used")
    if raw.startswith(("http://", "https://", "ssh://", "git@", "file://")):
        return raw
    if source == "github":
        return f"https://github.com/{raw.removesuffix('.git')}.git"
    if source == "gitee":
        return f"https://gitee.com/{raw.removesuffix('.git')}.git"
    return raw


def resolve_template_layout(root: Path) -> tuple[Path, Path | None]:
    root = root.expanduser().resolve()
    if not root.exists():
        raise TemplateSourceError(f"template_source_not_found:{root}")
    manifest = root / "manifest.json"
    template_dir = root / "template"
    if template_dir.is_dir():
        return template_dir, manifest if manifest.exists() else None
    kit = root / "mawflow_seed_kit"
    if (kit / "template").is_dir():
        kit_manifest = kit / "manifest.json"
        return kit / "template", kit_manifest if kit_manifest.exists() else None
    return root, manifest if manifest.exists() else None


def read_manifest(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TemplateSourceError(f"invalid_template_manifest:{path}") from exc
    if not isinstance(parsed, dict):
        raise TemplateSourceError(f"invalid_template_manifest:{path}")
    return parsed


def require_manifest(path: Path | None, *, source_type: str) -> dict[str, Any]:
    manifest = read_manifest(path)
    required = {"schema", "name", "version"}
    missing = sorted(required - set(manifest))
    if missing:
        raise TemplateSourceError(f"template_manifest_required:{source_type}:{','.join(missing)}")
    if manifest.get("schema") != SEED_KIT_MANIFEST_SCHEMA:
        raise TemplateSourceError(f"unsupported_template_manifest_schema:{manifest.get('schema') or 'missing'}")
    if manifest.get("name") != "mawflow-seed-kit" or manifest.get("contract_version") != 2:
        raise TemplateSourceError("seed_contract_v2_source_required")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(manifest.get("contract_fingerprint") or "")):
        raise TemplateSourceError("seed_contract_fingerprint_required")
    return manifest


def public_git_manifest(root: Path, *, ref: str) -> dict[str, Any] | None:
    """Validate and adapt the complete public Seed payload for Project Init.

    The Python data package uses ``manifest.json`` plus ``template/``. Public
    Git releases intentionally use a complete repository payload governed by
    ``PUBLIC_PAYLOAD_MANIFEST.json`` and ``TEMPLATE_VERSION`` instead. Keep the
    two distribution contracts distinct while exposing one versioned source
    model to Project Init.
    """

    payload_path = root / PUBLIC_PAYLOAD_MANIFEST
    if not payload_path.is_file():
        return None
    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TemplateSourceError(f"invalid_public_payload_manifest:{payload_path}") from exc
    if not isinstance(payload, dict) or payload.get("schema") != PUBLIC_PAYLOAD_SCHEMA:
        raise TemplateSourceError(
            f"unsupported_public_payload_schema:{payload.get('schema') if isinstance(payload, dict) else 'invalid'}"
        )
    if payload.get("contract_version") != 2:
        raise TemplateSourceError("public_payload_contract_v2_required")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(payload.get("contract_fingerprint") or "")):
        raise TemplateSourceError("public_payload_contract_fingerprint_required")
    bom = payload.get("bom")
    if not isinstance(bom, dict) or bom.get("contract") != "seed-contract-v2" or not str(bom.get("kit") or "").startswith("mawflow-seed-kit=="):
        raise TemplateSourceError("public_payload_bom_invalid")

    required_paths = payload.get("required_paths")
    forbidden_paths = payload.get("forbidden_paths")
    if not isinstance(required_paths, list) or not required_paths or not all(
        isinstance(item, str) and item.strip() for item in required_paths
    ):
        raise TemplateSourceError("public_payload_required_paths_invalid")
    if not isinstance(forbidden_paths, list) or not all(
        isinstance(item, str) and item.strip() for item in forbidden_paths
    ):
        raise TemplateSourceError("public_payload_forbidden_paths_invalid")
    missing = sorted(item for item in required_paths if not (root / item).is_file())
    if missing:
        raise TemplateSourceError(f"public_payload_required_path_missing:{missing[0]}")
    present = sorted(item for item in forbidden_paths if (root / item).exists())
    if present:
        raise TemplateSourceError(f"public_payload_forbidden_path_present:{present[0]}")

    version_path = root / "TEMPLATE_VERSION"
    if not version_path.is_file():
        raise TemplateSourceError("public_payload_template_version_missing")
    release_version = version_path.read_text(encoding="utf-8").strip()
    if not PUBLIC_VERSION_RE.fullmatch(release_version):
        raise TemplateSourceError("public_payload_template_version_invalid")
    if ref and PUBLIC_VERSION_RE.fullmatch(ref) and release_version.removeprefix("v") != ref.removeprefix("v"):
        raise TemplateSourceError(f"public_payload_ref_version_mismatch:{ref}:{release_version}")
    if str(payload.get("seed_version") or "") != release_version.removeprefix("v"):
        raise TemplateSourceError("public_payload_seed_version_mismatch")

    return {
        "schema": SEED_KIT_MANIFEST_SCHEMA,
        "name": "mawflow-seed-kit",
        "version": release_version.removeprefix("v"),
        "contract_version": 2,
        "contract_fingerprint": str(payload.get("contract_fingerprint") or ""),
        "public_release_version": release_version,
        "public_payload_schema": PUBLIC_PAYLOAD_SCHEMA,
    }


def template_tree_sha256(template_dir: Path) -> str:
    """Return a stable digest for the exact public template tree."""

    digest = hashlib.sha256()
    ignored_dirs = {".git", ".local", "__pycache__", ".pytest_cache", ".mypy_cache"}
    ignored_files = {".DS_Store"}
    for path in sorted(template_dir.rglob("*"), key=lambda item: item.relative_to(template_dir).as_posix()):
        relative = path.relative_to(template_dir).as_posix()
        if any(part in ignored_dirs for part in path.relative_to(template_dir).parts) or path.name in ignored_files:
            continue
        if path.is_symlink():
            raise TemplateSourceError(f"template_symlink_not_allowed:{relative}")
        if not path.is_file():
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def materialize_package_source(config: TemplateSourceConfig) -> MaterializedTemplate:
    # An unversioned daily init uses the installed, verified Seed. It must not
    # silently fetch a newer template or require connectivity/account access.
    installed_root = Path(__file__).resolve().parents[1]
    installed_manifest = require_manifest(installed_root / "manifest.json", source_type="package")
    if config.template == DEFAULT_TEMPLATE_PACKAGE and (
        not config.template_version or config.template_version == installed_manifest["version"]
    ):
        template_dir = installed_root / "template"
        return MaterializedTemplate(
            template_dir=template_dir,
            manifest_path=installed_root / "manifest.json",
            metadata={
                "source_type": "package",
                "package": DEFAULT_TEMPLATE_PACKAGE,
                "version": installed_manifest["version"],
                "source_commit": str(installed_manifest.get("source_commit") or ""),
                "index_url": config.index_url,
                "requirement": package_requirement(DEFAULT_TEMPLATE_PACKAGE, installed_manifest["version"]),
                "manifest_schema": installed_manifest["schema"],
                "template_tree_sha256": template_tree_sha256(template_dir),
                "installed_cache": True,
            },
        )
    cleanup = tempfile.TemporaryDirectory(prefix="mawflow-seed-kit-")
    tmp = Path(cleanup.name)
    target = tmp / "site-packages"
    requirement = package_requirement(config.template, config.template_version)
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--target",
        str(target),
        "--no-deps",
        "--index-url",
        config.index_url,
        requirement,
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        cleanup.cleanup()
        raise TemplateSourceError(completed.stderr.strip() or completed.stdout.strip() or "template_package_install_failed")
    template_dir, manifest_path = resolve_template_layout(target)
    manifest = require_manifest(manifest_path, source_type="package")
    tree_sha256 = template_tree_sha256(template_dir)
    return MaterializedTemplate(
        template_dir=template_dir,
        manifest_path=manifest_path,
        cleanup=cleanup,
        metadata={
            "source_type": "package",
            "package": config.template,
            "version": config.template_version or str(manifest.get("version") or "latest"),
            "source_commit": str(manifest.get("source_commit") or ""),
            "index_url": config.index_url,
            "requirement": requirement,
            "manifest_schema": manifest["schema"],
            "template_tree_sha256": tree_sha256,
        },
    )


def materialize_local_source(config: TemplateSourceConfig) -> MaterializedTemplate:
    if not config.path:
        raise TemplateSourceError("--path is required when --source local is used")
    template_dir, manifest_path = resolve_template_layout(Path(config.path))
    manifest = require_manifest(manifest_path, source_type="local")
    tree_sha256 = template_tree_sha256(template_dir)
    return MaterializedTemplate(
        template_dir=template_dir,
        manifest_path=manifest_path,
        metadata={
            "source_type": "local",
            "path": str(Path(config.path).expanduser().resolve()),
            "version": str(manifest.get("version") or ""),
            "manifest_schema": manifest["schema"],
            "template_tree_sha256": tree_sha256,
        },
    )


def materialize_git_source(config: TemplateSourceConfig) -> MaterializedTemplate:
    cleanup = tempfile.TemporaryDirectory(prefix="mawflow-seed-git-")
    tmp = Path(cleanup.name)
    repo_url = normalize_git_repo(config.source, config.repo)
    clone_target = tmp / "repo"
    if repo_url.startswith("http://"):
        cleanup.cleanup()
        raise TemplateSourceError("insecure_template_repo_url_use_https_or_ssh")
    command = ["git", "clone", "--filter=blob:none"]
    if config.ref:
        command.extend(["--branch", config.ref])
    command.extend([repo_url, str(clone_target)])
    try:
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
            env=config.git_env,
        )
    except subprocess.TimeoutExpired as exc:
        cleanup.cleanup()
        raise TemplateSourceError("template_git_clone_timed_out") from exc
    if completed.returncode != 0:
        cleanup.cleanup()
        raise TemplateSourceError(completed.stderr.strip() or completed.stdout.strip() or "template_git_clone_failed")
    template_dir, manifest_path = resolve_template_layout(clone_target)
    manifest = read_manifest(manifest_path)
    public_manifest: dict[str, Any] | None = None
    if not manifest:
        public_manifest = public_git_manifest(clone_target, ref=config.ref)
        if public_manifest is not None:
            manifest = public_manifest
            template_dir = clone_target
            manifest_path = tmp / "public-seed-template-manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not manifest:
        manifest = require_manifest(manifest_path, source_type=config.source)
    elif manifest.get("schema") != SEED_KIT_MANIFEST_SCHEMA:
        raise TemplateSourceError(f"unsupported_template_manifest_schema:{manifest.get('schema') or 'missing'}")
    tree_sha256 = template_tree_sha256(template_dir)
    commit_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=clone_target,
        text=True,
        capture_output=True,
        check=False,
        env=config.git_env,
    )
    source_commit = commit_result.stdout.strip() if commit_result.returncode == 0 else ""
    return MaterializedTemplate(
        template_dir=template_dir,
        manifest_path=manifest_path,
        cleanup=cleanup,
        metadata={
            "source_type": config.source,
            "repo": repo_url,
            "ref": config.ref,
            "version": str(manifest.get("version") or config.ref or ""),
            "source_commit": source_commit,
            "manifest_schema": manifest["schema"],
            "template_tree_sha256": tree_sha256,
            "public_payload_schema": str(manifest.get("public_payload_schema") or ""),
            "public_release_version": str(manifest.get("public_release_version") or ""),
        },
    )


def materialize_template_source(config: TemplateSourceConfig) -> MaterializedTemplate:
    if config.source == "package":
        return materialize_package_source(config)
    if config.source == "local":
        return materialize_local_source(config)
    if config.source in {"github", "gitee", "git"}:
        return materialize_git_source(config)
    raise TemplateSourceError(f"unsupported_template_source:{config.source}")
