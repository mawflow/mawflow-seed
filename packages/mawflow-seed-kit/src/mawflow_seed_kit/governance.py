"""Trusted installed entry point for the portable project governance protocol."""
from importlib.resources import files
import importlib.util
from pathlib import Path
import sys


def project_governance(root: Path, project_key: str):
    name = "mawflow_seed_kit._project_governance"
    if name not in sys.modules:
        directory = Path(str(files("mawflow_seed_kit").joinpath("template/ops/scripts/maw_governance")))
        spec = importlib.util.spec_from_file_location(name, directory / "__init__.py", submodule_search_locations=[str(directory)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            for key in list(sys.modules):
                if key == name or key.startswith(name + "."):
                    sys.modules.pop(key, None)
            raise
    return sys.modules[name].Governance(root, project_key)
