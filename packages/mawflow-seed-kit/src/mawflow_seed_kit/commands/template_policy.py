"""One source policy for project scripts, portable CLI and Host consumers."""
from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any
from urllib.parse import urljoin, urlsplit
from urllib.request import urlopen
import zipfile

import yaml

from ..components import _repository_identity, _validate_external_directory
from ..compiler import _repository_url_valid

PUBLIC_REPOSITORIES = {
    "github.com/mawflow/mawflow-seed",
    "gitee.com/mawflow/mawflow-seed",
}
PUBLIC_GIT_URL = "https://github.com/mawflow/mawflow-seed.git"
PUBLIC_MANIFEST_URL = "https://raw.githubusercontent.com/mawflow/mawflow-seed/main/PUBLIC_PAYLOAD_MANIFEST.json"
PACKAGE_INDEX_URL = "https://mawflow.com/packages/simple/mawflow-seed-kit/"
STABLE_TAG = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
LIMIT = 8 * 1024 * 1024


class PolicyBlocked(RuntimeError):
    def __init__(self, status: str, message: str, *, channel: str = "public_seed", evidence: dict | None = None):
        super().__init__(message)
        self.status, self.channel, self.evidence = status, channel, evidence or {}


def _merge(base: dict, overlay: dict) -> dict:
    result = dict(base)
    for key, value in overlay.items():
        result[key] = _merge(result[key], value) if isinstance(result.get(key), dict) and isinstance(value, dict) else value
    return result


def _yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    if path.is_symlink():
        raise ValueError("template_policy_symlink_forbidden")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("template_policy_mapping_required")
    return payload


def load_domain(root: Path, domain: str, *, profile: str | None = None, local: bool = True) -> dict:
    if not re.fullmatch(r"[a-z0-9-]+", domain):
        raise ValueError("template_policy_domain_invalid")
    profile = profile or os.environ.get("MAW_PROFILE") or str(_yaml(root / ".maw/project.yaml").get("configuration_profiles", {}).get("default_profile") or "")
    if profile and not re.fullmatch(r"[A-Za-z0-9_-]+", profile):
        raise ValueError("template_policy_profile_invalid")
    result: dict = {}
    directories = [root / ".maw"] + ([root / ".local/.maw"] if local else [])
    for directory in directories:
        suffixes = [""] + ([f".{profile}"] if profile and profile != "local" else []) + ([".local"] if local else [])
        for suffix in suffixes:
            paths = [directory / f"{domain}{suffix}.yaml", directory / f"{domain}{suffix}.yml"]
            paths += sorted((directory / f"{domain}{suffix}.d").glob("*.yaml"))
            paths += sorted((directory / f"{domain}{suffix}.d").glob("*.yml"))
            for path in paths:
                layer = _yaml(path)
                enabled = layer.pop("enabled", True)
                if enabled is False or (isinstance(enabled, str) and enabled.lower() in {"false", "0", "no", "off", "disabled"}):
                    continue
                result = _merge(result, layer)
    return result


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError("template_source_git_operation_failed")
    return result.stdout.strip()


def is_main_repository(root: Path) -> bool:
    # Local overlays cannot grant the platform-only development-source exception.
    project = load_domain(root, "project", local=False).get("project", {})
    identity = load_domain(root, "repository-identity", local=False).get("current_repository", {})
    if not (project.get("key") == "multiagentworker" and project.get("type") == "maw_control_plane"
            and identity.get("repository_key") == "multiagentworker" and identity.get("primary_role") == "main_repository"
            and (root / "code/orchestrator").is_dir() and (root / "code/node-runner").is_dir()):
        return False
    repository = load_domain(root, "repositories", local=False).get("repositories", {}).get("internal", {})
    try:
        return (Path(_git(root, "rev-parse", "--show-toplevel")).resolve() == root
                and _repository_identity(_git(root, "remote", "get-url", str(repository.get("remote_name") or "origin")))
                == _repository_identity(str(repository.get("url") or "")))
    except (RuntimeError, ValueError, subprocess.TimeoutExpired):
        return False


def resolve_main_source(root: Path, source: dict, *, target_version: str = "", source_path: str | None = None, git_url: str = "", profile: str | None = None, require_clean: bool = True) -> dict:
    key = str(source.get("repository_ref") or "")
    if not key:
        raise PolicyBlocked("seed_source_unbound", "主仓模板升级必须引用已登记的独立 Seed Git 代码源。", channel="internal_seed")
    registry = load_domain(root, "code-sources", profile=profile, local=False).get("code_sources", {})
    binding = load_domain(root, "code-source-bindings", profile=profile).get("code_source_bindings", {}).get(key, {})
    declaration = registry.get(key, {})
    components = load_domain(root, "components", local=False).get("components", [])
    if not any(isinstance(component, dict) and isinstance(component.get("source"), dict) and component["source"].get("mode") == "external_git"
               and component["source"].get("repository_ref") == key for component in components):
        raise PolicyBlocked("seed_source_unbound", "Seed 代码源必须由独立 external_git 工具组件引用。", channel="internal_seed")
    if not _repository_url_valid(str(declaration.get("repository_url") or "")):
        raise PolicyBlocked("seed_source_invalid", "Seed 代码源地址非法或包含凭据。", channel="internal_seed")
    directory = str(binding.get("directory_path") or "")
    if not directory or not declaration.get("repository_url"):
        raise PolicyBlocked("seed_source_unbound", "Seed 独立 Git 目录未绑定；先补全并绑定代码源，不回退到远端临时克隆或当前主仓。", channel="internal_seed")
    if (git_url or source.get("git_url")) and _repository_identity(git_url or str(source["git_url"])) != _repository_identity(declaration["repository_url"]):
        raise PolicyBlocked("source_policy_violation", "指定来源与登记的 Seed 仓身份不一致。", channel="internal_seed")
    override = source_path if source_path is not None else str(source.get("local_path") or "")
    if override:
        override_path = Path(override).expanduser()
        override_path = override_path if override_path.is_absolute() else root / override_path
        if override_path.resolve() != Path(directory).expanduser().resolve():
            raise PolicyBlocked("source_policy_violation", "本机覆盖必须与 Seed 代码源绑定指向同一目录。", channel="internal_seed")
    try:
        repo, _ = _validate_external_directory(directory, repository_url=declaration["repository_url"], project_root=root)
        if require_clean and _git(repo, "status", "--porcelain"):
            raise PolicyBlocked("seed_source_dirty", "Seed 工作副本存在未提交改动；先提交并验证候选，升级只读取固定 commit。", channel="internal_seed")
        role = _yaml(repo / ".maw-template/template.yaml").get("template", {}).get("repository_role")
        if role != "maw_project_seed_repository":
            raise ValueError("seed_repository_role_mismatch")
    except (ValueError, RuntimeError) as exc:
        if isinstance(exc, PolicyBlocked):
            raise
        raise PolicyBlocked("seed_source_invalid", "Seed 目录缺失、未被外层 Git 忽略或仓库身份不匹配。", channel="internal_seed") from exc
    return {"repo": repo, "source_channel": "internal_seed", "source_kind": "registered_git_directory",
            "git_url": declaration["repository_url"], "target_version": target_version or str(source.get("version") or "HEAD")}


def _read_url(url: str) -> bytes:
    with urlopen(url, timeout=30) as response:
        payload = response.read(LIMIT + 1)
    if len(payload) > LIMIT:
        raise ValueError("public_release_metadata_too_large")
    return payload


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.extend(value for key, value in attrs if key == "href" and value)


def verify_public_kit(version: str, manifest: dict) -> dict:
    links = _Links()
    links.feed(_read_url(PACKAGE_INDEX_URL).decode("utf-8"))
    name = f"mawflow_seed_kit-{version}-py3-none-any.whl"
    for href in links.links:
        url = urljoin(PACKAGE_INDEX_URL, href)
        parsed, index = urlsplit(url), urlsplit(PACKAGE_INDEX_URL)
        digest = parsed.fragment.removeprefix("sha256=")
        if (parsed.scheme != "https" or parsed.netloc != index.netloc or parsed.username or parsed.query
                or parsed.path != index.path + name or not re.fullmatch(r"[a-f0-9]{64}", digest)):
            continue
        wheel = _read_url(url.split("#", 1)[0])
        if hashlib.sha256(wheel).hexdigest() != digest:
            raise ValueError("public_seed_kit_checksum_mismatch")
        with zipfile.ZipFile(io.BytesIO(wheel)) as archive:
            info = archive.getinfo("mawflow_seed_kit/manifest.json")
            if info.file_size > LIMIT:
                raise ValueError("public_seed_kit_manifest_too_large")
            kit = json.loads(archive.read(info))
        if not (kit.get("version") == version and kit.get("contract_version") == manifest.get("contract_version")
                and kit.get("contract_fingerprint") == manifest.get("contract_fingerprint")):
            raise ValueError("public_seed_kit_version_family_mismatch")
        return {"version": version, "sha256": digest, "artifact_url": url.split("#", 1)[0]}
    raise ValueError("public_seed_kit_not_published")


def _clone_public(repo: Path, git_url: str) -> None:
    _git(repo.parent, "clone", "--quiet", "--bare", "--filter=blob:none", git_url, str(repo))


def _git_file(repo: Path, commit: str, path: str) -> bytes:
    result = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=repo, capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError("public_release_file_missing")
    return result.stdout


def resolve_source(root: Path, source: dict, *, target_version: str = "", source_path: str | None = None, git_url: str = "", profile: str | None = None) -> dict:
    if is_main_repository(root):
        if source.get("source_channel") != "internal_seed":
            raise PolicyBlocked("source_policy_violation", "主仓模板升级只读取已绑定的 Seed Git 目录。", channel="internal_seed")
        return resolve_main_source(root, source, target_version=target_version, source_path=source_path, git_url=git_url, profile=profile)
    if source_path or source.get("local_path"):
        raise PolicyBlocked("source_policy_violation", "其它派生项目只能采用公共发布版本，本机目录不能覆盖升级来源。")
    if source.get("source_channel") == "internal_seed":
        raise PolicyBlocked("public_source_migration_required", "此项目仍记录内部来源；先保留旧基线及来源，按版本、契约和公开载荷证据完成来源迁移预览。")
    if source.get("source_channel") not in {None, "", "public_seed"} or (not source.get("source_channel") and source.get("kind") != "package"):
        raise PolicyBlocked("source_channel_unconfirmed", "历史来源尚未确认；核对来源证据后迁移到公共发布路线。")
    git_url = git_url or str(source.get("git_url") or PUBLIC_GIT_URL)
    try:
        if _repository_identity(git_url) not in PUBLIC_REPOSITORIES or urlsplit(git_url).scheme != "https" or urlsplit(git_url).username or urlsplit(git_url).query or urlsplit(git_url).fragment:
            raise ValueError("non_public_repository")
    except ValueError as exc:
        raise PolicyBlocked("source_policy_violation", "升级来源必须是官方公共 Seed 仓的无凭据 HTTPS 地址。") from exc
    requested = target_version or str(source.get("version") or "latest_verified_stable")
    if requested not in {"latest_verified_stable", "latest-stable"} and not STABLE_TAG.fullmatch(requested):
        raise PolicyBlocked("public_release_required", "公共升级只接受已发布稳定 tag，不能采用 main、开发分支、rc 或任意 commit。")
    temporary = tempfile.TemporaryDirectory(prefix="mawflow-public-seed-")
    try:
        if requested in {"latest_verified_stable", "latest-stable"}:
            announcement = json.loads(_read_url(PUBLIC_MANIFEST_URL))
            requested = "v" + str(announcement.get("seed_version") or "")
        if not STABLE_TAG.fullmatch(requested):
            raise ValueError("public_stable_tag_invalid")
        repo = Path(temporary.name) / "source.git"
        _clone_public(repo, git_url)
        commit = _git(repo, "rev-parse", "--verify", f"refs/tags/{requested}^{{commit}}")
        manifest_bytes = _git_file(repo, commit, "PUBLIC_PAYLOAD_MANIFEST.json")
        manifest = json.loads(manifest_bytes)
        version = requested[1:]
        lock = yaml.safe_load(_git(repo, "show", f"{commit}:.maw/seed.lock"))
        if not (manifest.get("schema") == "mawflow.seed_public_payload.v2" and manifest.get("seed_version") == version
                and manifest.get("bom", {}).get("kit") == f"mawflow-seed-kit=={version}"
                and _git(repo, "show", f"{commit}:TEMPLATE_VERSION") == requested
                and lock.get("seed_version") == version and lock.get("bom", {}).get("kit") == f"mawflow-seed-kit=={version}"
                and type(manifest.get("contract_version")) is int and manifest["contract_version"] == int(version.split(".")[0])
                and re.fullmatch(r"sha256:[a-f0-9]{64}", str(manifest.get("contract_fingerprint") or ""))
                and all(lock.get(key) == manifest.get(key) for key in ("contract_version", "contract_fingerprint"))):
            raise ValueError("public_seed_version_family_mismatch")
        kit = verify_public_kit(version, manifest)
        return {"repo": repo, "temporary_directory": temporary, "source_channel": "public_seed",
                "source_kind": "verified_public_release", "git_url": git_url, "public_git_url": PUBLIC_GIT_URL,
                "target_version": requested, "release": {"version": version, "tag": requested, "commit": commit,
                "contract_version": manifest["contract_version"], "contract_fingerprint": manifest["contract_fingerprint"],
                "payload_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(), "kit": kit, "status": "verified"}}
    except Exception as exc:
        temporary.cleanup()
        raise PolicyBlocked("public_release_unavailable", "公共 tag、载荷或同版本 Kit 未通过回读校验；保持原项目，不能回退到内部候选源。") from exc
