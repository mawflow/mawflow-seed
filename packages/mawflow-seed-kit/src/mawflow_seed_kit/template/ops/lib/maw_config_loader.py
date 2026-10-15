"""MAW project configuration loader with .local overlay support."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from string import Formatter
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment guard
    raise RuntimeError("PyYAML is required for MAW config loading") from exc


DOMAIN_RE = re.compile(r"^[A-Za-z0-9_-]+$")
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
LOGICAL_KEY_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class ConfigPathError(ValueError):
    """Raised when a requested project path is unsafe."""


class ConfigKeyIndexError(ValueError):
    """Raised when a logical config key cannot be resolved safely."""


class MawConfigLoader:
    """Load MAW configuration domains with profile and .local overlays."""

    def __init__(
        self,
        project_root: Union[str, os.PathLike[str]] = ".",
        profile: Optional[str] = None,
        include_maw_local: bool = True,
        include_local_overlay: bool = True,
    ) -> None:
        self.project_root = Path(project_root).expanduser().resolve()
        self.profile = profile if profile is not None else os.environ.get("MAW_PROFILE")
        self.include_maw_local = include_maw_local
        self.include_local_overlay = include_local_overlay
        self._loaded_layers: Dict[str, List[Path]] = {}

    def get(self, domain: str, key: Optional[str] = None, default: Any = None) -> Any:
        data = self.load_domain(domain)
        if not key:
            return data
        value = read_dotted_path(data, key)
        return default if value is None else value

    def get_or_read(
        self,
        domain: str,
        key: str,
        fallback_path: str,
        default: Any = None,
        parser: str = "auto",
    ) -> Any:
        value = self.get(domain, key)
        if value is not None:
            return value

        path = self.resolve_project_path(fallback_path)
        if not path.exists():
            return default

        return self.read_file(fallback_path, parser=parser)

    def explain(self, domain: str, key: Optional[str] = None) -> Dict[str, Any]:
        data = self.load_domain(domain)
        value = read_dotted_path(data, key) if key else data
        return {
            "domain": domain,
            "key": key,
            "value": value,
            "layers": [str(path.relative_to(self.project_root)) for path in self._loaded_layers.get(domain, [])],
        }

    def load_domain(self, domain: str) -> Dict[str, Any]:
        validate_domain(domain)
        profile = self._effective_profile()
        layers = self._domain_layers(domain, profile)
        merged: Dict[str, Any] = {}

        for path in layers:
            layer = load_yaml_file(path)
            if not config_layer_enabled(layer):
                continue
            merged = deep_merge(merged, strip_config_layer_metadata(layer))

        self._loaded_layers[domain] = layers
        return merged

    def read_file(self, path: str, parser: str = "auto") -> Any:
        resolved = self.resolve_project_path(path)
        if not resolved.is_file():
            raise FileNotFoundError(str(resolved))

        parser = detect_parser(resolved) if parser == "auto" else parser
        text = resolved.read_text(encoding="utf-8")

        if parser == "text":
            return text
        if parser == "markdown":
            return text
        if parser == "yaml":
            return yaml.safe_load(text) or {}
        if parser == "json":
            return json.loads(text)
        if parser == "env":
            return parse_env(text)
        if parser == "toml":
            return parse_toml(text)

        raise ValueError(f"Unsupported parser: {parser}")

    def resolve_project_path(self, path: str) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            raise ConfigPathError(f"Path must be project-root relative: {path}")

        parts = candidate.parts
        if not parts or any(part in ("", ".", "..") for part in parts):
            raise ConfigPathError(f"Unsafe project path: {path}")

        if parts[0] in {".git", ".ssh"}:
            raise ConfigPathError(f"Refusing to read protected path: {path}")

        forbidden_prefixes = {
            "node_modules",
            "dist",
            "build",
            "coverage",
            "runtime",
            "logs",
            "tmp",
            "cache",
        }
        if parts[0] in forbidden_prefixes:
            raise ConfigPathError(f"Refusing to read generated path: {path}")

        if not all(SAFE_SEGMENT_RE.match(part) for part in parts):
            raise ConfigPathError(f"Unsafe path segment in: {path}")

        resolved = (self.project_root / candidate).resolve()
        if not resolved.is_relative_to(self.project_root):
            raise ConfigPathError(f"Path escapes project root: {path}")
        return resolved

    def _effective_profile(self) -> str:
        if self.profile:
            validate_profile(self.profile)
            return self.profile

        project_path = self.project_root / ".maw" / "project.yaml"
        if not project_path.is_file():
            return ""

        project_config = load_yaml_file(project_path)
        profile = read_dotted_path(project_config, "configuration_profiles.default_profile") or ""
        if profile:
            validate_profile(str(profile))
        return str(profile)

    def _domain_layers(self, domain: str, profile: str) -> List[Path]:
        layers: List[Path] = []
        maw_dir = self.project_root / ".maw"
        local_maw_dir = self.project_root / ".local" / ".maw"

        layers.extend(yaml_layer_files(maw_dir, domain, ""))

        if profile and profile != "local":
            layers.extend(yaml_layer_files(maw_dir, domain, f".{profile}"))

        if self.include_maw_local:
            layers.extend(yaml_layer_files(maw_dir, domain, ".local"))

        if self.include_local_overlay:
            layers.extend(yaml_layer_files(local_maw_dir, domain, ""))
            if profile and profile != "local":
                layers.extend(yaml_layer_files(local_maw_dir, domain, f".{profile}"))
            layers.extend(yaml_layer_files(local_maw_dir, domain, ".local"))

        return layers


class MawLogicalKeyResolver:
    """Resolve stable logical keys to MAW config values or safe project files."""

    def __init__(
        self,
        project_root: Union[str, os.PathLike[str]] = ".",
        profile: Optional[str] = None,
        include_maw_local: bool = True,
        include_local_overlay: bool = True,
    ) -> None:
        self.loader = MawConfigLoader(
            project_root=project_root,
            profile=profile,
            include_maw_local=include_maw_local,
            include_local_overlay=include_local_overlay,
        )
        self._index_cache: Optional[Dict[str, Any]] = None

    @property
    def project_root(self) -> Path:
        return self.loader.project_root

    def get(self, logical_key: str, params: Optional[Dict[str, str]] = None) -> Any:
        return self.resolve(logical_key, params=params)["value"]

    def explain(self, logical_key: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        return self.resolve(logical_key, params=params)["explain"]

    def resolve(self, logical_key: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        validate_logical_key(logical_key)
        index = self._load_index()
        keys = index["keys"]
        if logical_key not in keys:
            raise ConfigKeyIndexError(f"Unknown logical key: {logical_key}")

        params = normalize_params(params or {})
        entry = keys[logical_key]
        key_type = str(entry.get("type") or "").strip()
        if key_type == "config":
            value, detail = self._resolve_config(logical_key, entry)
        elif key_type == "config_template":
            value, detail = self._resolve_config_template(logical_key, entry, params)
        elif key_type == "file":
            value, detail = self._resolve_file(logical_key, entry)
        elif key_type == "file_template":
            value, detail = self._resolve_file_template(logical_key, entry, params)
        else:
            raise ConfigKeyIndexError(f"Unsupported logical key type for {logical_key}: {key_type!r}")

        explain = {
            "logical_key": logical_key,
            "type": key_type,
            "index_source": index["sources"].get(logical_key),
            "index_layers": index["layers"],
            "params": params,
            "include_maw_local": self.loader.include_maw_local,
            "include_local_overlay": self.loader.include_local_overlay,
            "value": value,
        }
        explain.update(detail)
        return {"value": value, "explain": explain}

    def _resolve_config(self, logical_key: str, entry: Dict[str, Any]) -> Tuple[Any, Dict[str, Any]]:
        domain = required_string(entry, "domain", logical_key)
        path = required_string(entry, "path", logical_key)
        self._ensure_config_entry_allowed(logical_key, domain, entry)
        value = self.loader.get(domain, path)
        if value is None:
            raise ConfigKeyIndexError(f"Config path not found for logical key {logical_key}: {domain}:{path}")
        return value, self._config_detail(domain, path)

    def _resolve_config_template(
        self,
        logical_key: str,
        entry: Dict[str, Any],
        params: Dict[str, str],
    ) -> Tuple[Any, Dict[str, Any]]:
        domain = required_string(entry, "domain", logical_key)
        path_template = required_string(entry, "path_template", logical_key)
        self._ensure_config_entry_allowed(logical_key, domain, entry)
        path = render_template(path_template, entry, params, logical_key)
        value = self.loader.get(domain, path)
        if value is None:
            raise ConfigKeyIndexError(f"Config path not found for logical key {logical_key}: {domain}:{path}")
        return value, self._config_detail(domain, path, path_template=path_template)

    def _resolve_file(self, logical_key: str, entry: Dict[str, Any]) -> Tuple[Any, Dict[str, Any]]:
        path = required_string(entry, "path", logical_key)
        return self._read_indexed_file(logical_key, entry, path)

    def _resolve_file_template(
        self,
        logical_key: str,
        entry: Dict[str, Any],
        params: Dict[str, str],
    ) -> Tuple[Any, Dict[str, Any]]:
        path_template = required_string(entry, "path_template", logical_key)
        path = render_template(path_template, entry, params, logical_key)
        value, detail = self._read_indexed_file(logical_key, entry, path)
        detail["path_template"] = path_template
        return value, detail

    def _read_indexed_file(self, logical_key: str, entry: Dict[str, Any], path: str) -> Tuple[Any, Dict[str, Any]]:
        parser = str(entry.get("parser") or "text").strip()
        validate_logical_file_parser(parser, logical_key)
        max_bytes = int(entry.get("max_bytes") or 65536)
        if max_bytes <= 0:
            raise ConfigKeyIndexError(f"max_bytes must be positive for logical key {logical_key}")

        resolved = resolve_logical_file_path(self.project_root, path)
        if not resolved.is_file():
            raise FileNotFoundError(f"Logical key {logical_key} file not found: {path}")
        size = resolved.stat().st_size
        if size > max_bytes:
            raise ConfigKeyIndexError(
                f"Logical key {logical_key} file exceeds max_bytes: {path} ({size} > {max_bytes})"
            )

        text = resolved.read_text(encoding="utf-8")
        value = parse_logical_file_text(text, parser)
        return value, {
            "file_path": path,
            "parser": parser,
            "max_bytes": max_bytes,
            "bytes": size,
        }

    def _config_detail(
        self,
        domain: str,
        path: str,
        path_template: Optional[str] = None,
    ) -> Dict[str, Any]:
        detail = {
            "domain": domain,
            "path": path,
            "config_layers": [
                str(layer.relative_to(self.project_root)) for layer in self.loader._loaded_layers.get(domain, [])
            ],
        }
        if path_template is not None:
            detail["path_template"] = path_template
        return detail

    def _ensure_config_entry_allowed(self, logical_key: str, domain: str, entry: Dict[str, Any]) -> None:
        if domain == "secrets" and entry.get("allow_sensitive") is not True:
            raise ConfigKeyIndexError(
                f"Logical key {logical_key} maps to sensitive config domain 'secrets' without allow_sensitive"
            )

    def _load_index(self) -> Dict[str, Any]:
        if self._index_cache is not None:
            return self._index_cache

        keys: Dict[str, Dict[str, Any]] = {}
        sources: Dict[str, str] = {}
        layers: List[str] = []

        template_index = self.project_root / ".maw-template" / "config-key-index.yaml"
        if template_index.is_file():
            template_keys = extract_config_key_index(load_yaml_file(template_index), str(template_index.relative_to(self.project_root)))
            for key, entry in template_keys.items():
                keys[key] = entry
                sources[key] = str(template_index.relative_to(self.project_root))
            layers.append(str(template_index.relative_to(self.project_root)))

        project_doc = self.loader.load_domain("config-key-index")
        project_layers = [
            str(layer.relative_to(self.project_root)) for layer in self.loader._loaded_layers.get("config-key-index", [])
        ]
        layers.extend(project_layers)
        project_keys = extract_config_key_index(project_doc, "config-key-index")
        for key, entry in project_keys.items():
            if key in keys and keys[key].get("allow_project_override") is not True:
                raise ConfigKeyIndexError(
                    f"Project config-key-index cannot override reserved template logical key: {key}"
                )
            keys[key] = deep_merge(keys.get(key), entry) if key in keys else entry
            sources[key] = "project:config-key-index"

        if not layers:
            raise ConfigKeyIndexError(
                "No config key index files found; expected .maw-template/config-key-index.yaml "
                "or .maw/config-key-index.yaml"
            )

        self._index_cache = {"keys": keys, "sources": sources, "layers": layers}
        return self._index_cache


def validate_domain(domain: str) -> None:
    if not DOMAIN_RE.match(domain):
        raise ValueError(f"Invalid config domain: {domain!r}")


def validate_profile(profile: str) -> None:
    if profile and not DOMAIN_RE.match(profile):
        raise ValueError(f"Invalid config profile: {profile!r}")


def validate_logical_key(logical_key: str) -> None:
    if not LOGICAL_KEY_RE.match(logical_key):
        raise ConfigKeyIndexError(f"Invalid logical key: {logical_key!r}")


def load_yaml_file(path: Path) -> Dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def config_layer_enabled(data: Any) -> bool:
    if not isinstance(data, dict):
        return True
    value = data.get("enabled")
    if value is False:
        return False
    if isinstance(value, str) and value.strip().lower() in {"false", "0", "no", "off", "disabled"}:
        return False
    return True


def strip_config_layer_metadata(data: Any) -> Any:
    if not isinstance(data, dict) or "enabled" not in data:
        return data
    cleaned = dict(data)
    cleaned.pop("enabled", None)
    return cleaned


def yaml_layer_files(root: Path, domain: str, suffix: str) -> List[Path]:
    files: List[Path] = []
    for ext in (".yaml", ".yml"):
        path = root / f"{domain}{suffix}{ext}"
        if path.is_file():
            files.append(path)

    fragment_dir = root / f"{domain}{suffix}.d"
    if fragment_dir.is_dir():
        files.extend(sorted(fragment_dir.glob("*.yaml")))
        files.extend(sorted(fragment_dir.glob("*.yml")))

    return files


def keyed_hash_array(value: Sequence[Any]) -> bool:
    return all(isinstance(item, dict) and "key" in item for item in value)


def merge_arrays(base: Sequence[Any], override: Sequence[Any]) -> List[Any]:
    if keyed_hash_array(base) and keyed_hash_array(override):
        merged = [dict(item) for item in base]
        index = {item["key"]: idx for idx, item in enumerate(merged)}

        for item in override:
            key = item["key"]
            if key in index:
                merged[index[key]] = deep_merge(merged[index[key]], item)
            else:
                index[key] = len(merged)
                merged.append(dict(item))
        return merged

    if all(not isinstance(item, dict) for item in base) and all(not isinstance(item, dict) for item in override):
        merged = list(base)
        for item in override:
            if item not in merged:
                merged.append(item)
        return merged

    return list(override)


def deep_merge(base: Any, override: Any) -> Any:
    if base is None:
        return override
    if override is None:
        return base

    if isinstance(base, dict) and isinstance(override, dict):
        merged = dict(base)
        for key, value in override.items():
            merged[key] = deep_merge(merged.get(key), value)
        return merged

    if isinstance(base, list) and isinstance(override, list):
        return merge_arrays(base, override)

    return override


def read_dotted_path(data: Any, dotted_path: Optional[str]) -> Any:
    if not dotted_path:
        return data

    current = data
    for segment in dotted_path.split("."):
        if isinstance(current, dict):
            current = current.get(segment)
        elif isinstance(current, list) and segment.isdigit():
            index = int(segment)
            current = current[index] if index < len(current) else None
        else:
            return None

        if current is None:
            return None

    return current


def extract_config_key_index(data: Dict[str, Any], source: str) -> Dict[str, Dict[str, Any]]:
    raw_keys = (data.get("config_key_index") or {}).get("keys") if isinstance(data, dict) else None
    if raw_keys is None and isinstance(data, dict):
        raw_keys = data.get("keys")
    if raw_keys is None:
        return {}
    if not isinstance(raw_keys, dict):
        raise ConfigKeyIndexError(f"config_key_index.keys must be a mapping in {source}")

    keys: Dict[str, Dict[str, Any]] = {}
    for key, entry in raw_keys.items():
        validate_logical_key(str(key))
        if not isinstance(entry, dict):
            raise ConfigKeyIndexError(f"Logical key entry must be a mapping in {source}: {key}")
        keys[str(key)] = dict(entry)
    return keys


def normalize_params(params: Dict[str, str]) -> Dict[str, str]:
    normalized: Dict[str, str] = {}
    for raw_key, raw_value in params.items():
        key = raw_key.replace("-", "_")
        if not key or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", key):
            raise ConfigKeyIndexError(f"Invalid parameter name: {raw_key!r}")
        value = str(raw_value)
        if not value or not SAFE_SEGMENT_RE.match(value):
            raise ConfigKeyIndexError(f"Unsafe parameter value for {key}: {value!r}")
        normalized[key] = value
    return normalized


def required_string(entry: Dict[str, Any], field: str, logical_key: str) -> str:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ConfigKeyIndexError(f"Logical key {logical_key} requires non-empty field: {field}")
    return value.strip()


def render_template(
    template: str,
    entry: Dict[str, Any],
    params: Dict[str, str],
    logical_key: str,
) -> str:
    required_params = [str(item) for item in entry.get("required_params") or []]
    template_params = [
        field_name for _, field_name, _, _ in Formatter().parse(template) if field_name is not None and field_name != ""
    ]
    for name in sorted(set(required_params + template_params)):
        if name not in params:
            raise ConfigKeyIndexError(f"Logical key {logical_key} requires parameter: {name}")
    try:
        return template.format(**params)
    except KeyError as exc:
        raise ConfigKeyIndexError(f"Logical key {logical_key} missing parameter: {exc.args[0]}") from exc


def validate_logical_file_parser(parser: str, logical_key: str) -> None:
    if parser not in {"text", "yaml", "json", "env", "toml", "markdown"}:
        raise ConfigKeyIndexError(f"Unsupported file parser for logical key {logical_key}: {parser}")


def resolve_logical_file_path(root: Path, path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        raise ConfigPathError(f"Path must be project-root relative: {path}")
    parts = candidate.parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise ConfigPathError(f"Unsafe project path: {path}")
    forbidden_prefixes = {
        ".git",
        ".ssh",
        ".local",
        "artifacts",
        "build",
        "cache",
        "coverage",
        "dist",
        "logs",
        "node_modules",
        "runtime",
        "tmp",
        "vendor",
        "workspaces",
    }
    if parts[0] in forbidden_prefixes:
        raise ConfigPathError(f"Refusing to read protected or generated path: {path}")
    if candidate.name.startswith(".env") or "secrets" in candidate.name.lower():
        raise ConfigPathError(f"Refusing to read sensitive path: {path}")
    if not all(SAFE_SEGMENT_RE.match(part) for part in parts):
        raise ConfigPathError(f"Unsafe path segment in: {path}")
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(root):
        raise ConfigPathError(f"Path escapes project root: {path}")
    return resolved


def parse_logical_file_text(text: str, parser: str) -> Any:
    if parser in {"text", "markdown"}:
        return text
    if parser == "yaml":
        return yaml.safe_load(text) or {}
    if parser == "json":
        return json.loads(text)
    if parser == "env":
        return parse_env(text)
    if parser == "toml":
        return parse_toml(text)
    raise ValueError(f"Unsupported parser: {parser}")


def detect_parser(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        return "yaml"
    if suffix == ".json":
        return "json"
    if suffix == ".toml":
        return "toml"
    if path.name.startswith(".env") or suffix == ".env":
        return "env"
    return "text"


def parse_env(text: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def parse_toml(text: str) -> Dict[str, Any]:
    try:
        import tomllib  # type: ignore
    except ImportError:  # pragma: no cover - Python < 3.11 fallback
        try:
            import tomli as tomllib  # type: ignore
        except ImportError as exc:
            raise RuntimeError("tomllib or tomli is required to parse TOML files") from exc

    return tomllib.loads(text)
