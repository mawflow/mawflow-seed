from .catalog import CONTRACT_VERSION, SEED_VERSION, catalog, contract_fingerprint, public_catalog
from .compiler import compile_project_definition
from .components import (
    apply_component_plan,
    inspect_components,
    plan_component_init,
    plan_component_remove,
    plan_component_source_binding,
    plan_component_source_unbind,
    plan_component_state,
)
from .changes import apply_change_plan, plan_change_set, plan_contract_repair
from .migration import apply_migration_plan, plan_migration, rollback_migration
from .project_topology import (
    apply_topology_plan,
    default_managed_clone_path,
    inspect_project_sources,
    plan_code_source_binding,
    plan_code_source_remove,
    plan_code_source_unbind,
    plan_code_source_upsert,
    plan_source_registry_consolidation,
    plan_subproject_remove,
    plan_subproject_upsert,
)
from .template import materialize_project

__all__ = [
    "CONTRACT_VERSION",
    "SEED_VERSION",
    "apply_change_plan",
    "apply_component_plan",
    "apply_migration_plan",
    "apply_topology_plan",
    "catalog",
    "compile_project_definition",
    "contract_fingerprint",
    "default_managed_clone_path",
    "inspect_components",
    "inspect_project_sources",
    "materialize_project",
    "plan_change_set",
    "plan_component_init",
    "plan_component_remove",
    "plan_component_source_binding",
    "plan_component_source_unbind",
    "plan_component_state",
    "plan_code_source_binding",
    "plan_code_source_remove",
    "plan_code_source_unbind",
    "plan_code_source_upsert",
    "plan_contract_repair",
    "plan_migration",
    "plan_source_registry_consolidation",
    "plan_subproject_remove",
    "plan_subproject_upsert",
    "public_catalog",
    "rollback_migration",
]

__version__ = "2.5.0"
