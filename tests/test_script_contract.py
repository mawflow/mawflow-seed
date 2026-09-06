from __future__ import annotations

from mawflow_seed_kit import public_script_contract


def test_public_script_contract_exposes_workbench_groups_and_readiness_gates() -> None:
    contract = public_script_contract()

    assert contract["schema"] == "mawflow.seed_script_contract.v1"
    assert contract["canonical_local_development_script"] == "dev"
    assert contract["readiness_gates"] == [
        "development_service_selection_configured",
        "selected_services_have_real_commands",
        "canonical_dev_script_connected",
        "successful_background_start_recorded",
    ]
    groups = {item["key"]: item for item in contract["groups"]}
    assert groups["local_debug"]["execution_modes"]["dev"] == "background_development"
    assert groups["verification"]["default_execution_mode"] == "confirmed_environment_action"
    assert groups["delivery_operations"]["default_execution_mode"] == "terminal_only"


def test_public_script_contract_returns_an_independent_copy() -> None:
    first = public_script_contract()
    first["groups"][0]["label"] = "changed"

    assert public_script_contract()["groups"][0]["label"] == "本地调试"
