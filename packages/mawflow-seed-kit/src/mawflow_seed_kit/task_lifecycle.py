"""Validate optional task lifecycle declarations; never control live resources."""
from __future__ import annotations

from typing import Any, Callable

from .standard_evidence import nonempty, SHA256

STAGES = {"scoped", "preparing", "executing", "verifying", "closing", "ended"}
OUTCOMES = {"pending", "succeeded", "partial", "failed", "cancelled", "interrupted"}
RESOURCE_STATES = {"active", "released", "retained", "pending_automatic", "failed", "unknown"}


def validate_lifecycle(task: dict[str, Any], receipt_valid: Callable[[Any, str], bool]) -> list[str]:
    """Return safe issue codes. Receipts are checked by the existing evidence owner."""
    if "lifecycle" not in task:
        return []
    value = task["lifecycle"]
    if not isinstance(value, dict):
        return ["lifecycle_invalid"]
    issues: list[str] = []
    if value.get("schema") != "mawflow.task_lifecycle.v1":
        issues.append("lifecycle_schema_invalid")
    protocol = value.get("protocol_revision", 1)
    if type(protocol) is not int or protocol not in {1, 2}:
        issues.append("lifecycle_protocol_invalid")
    revision = value.get("scope_revision")
    if type(revision) is not int or revision < 1:
        issues.append("lifecycle_scope_revision_invalid")
    run = value.get("run_ref")
    if not isinstance(run, str) or not run.strip():
        issues.append("lifecycle_run_missing")
    stage, outcome = value.get("stage"), value.get("outcome")
    if stage not in STAGES or outcome not in OUTCOMES:
        issues.append("lifecycle_state_invalid")
    condition = value.get("condition")
    if condition not in {"active", "blocked", "waiting_human", "paused"}:
        issues.append("lifecycle_condition_invalid")
    if condition != "active" and not value.get("reason_ref"):
        issues.append("lifecycle_wait_reason_missing")
    if condition == "paused" and not value.get("pause_authorization_ref"):
        issues.append("lifecycle_pause_authorization_missing")
    if (stage == "ended") != (outcome != "pending"):
        issues.append("lifecycle_outcome_stage_mismatch")
    if protocol == 2 and outcome in {"partial", "failed", "cancelled", "interrupted"} and not nonempty(value.get("outcome_reason_ref")):
        issues.append("lifecycle_outcome_reason_missing")
    if "continuation" in value:
        continuation = value["continuation"]
        if (not isinstance(continuation, dict)
                or any(not nonempty(continuation.get(field)) for field in ("previous_run_ref", "checkpoint_ref", "ownership_check_ref"))
                or continuation.get("previous_run_ref") == run):
            issues.append("lifecycle_continuation_invalid")
    criteria = value.get("completion_criteria")
    if not isinstance(criteria, list) or not criteria:
        issues.append("lifecycle_criteria_missing")
        criteria = []
    seen: set[str] = set()
    for item in criteria:
        if (not isinstance(item, dict) or not isinstance(item.get("key"), str)
                or not item["key"] or item["key"] in seen
                or item.get("status") not in {"pending", "passed", "failed", "not_applicable"}):
            issues.append("lifecycle_criterion_invalid")
            continue
        seen.add(item["key"])
        refs = item.get("evidence_refs", [])
        valid_refs = isinstance(refs, list) and bool(refs) and all(
            isinstance(ref, str) and ref in task.get("_valid_evidence_keys", set()) for ref in refs)
        if item["status"] == "passed" and not valid_refs:
            issues.append("lifecycle_criterion_evidence_missing")
        if item["status"] == "not_applicable" and not item.get("reason"):
            issues.append("lifecycle_criterion_reason_missing")
    closure = value.get("task_closure")
    if closure not in {"open", "ready_for_review", "closed", "cancelled"}:
        issues.append("lifecycle_closure_invalid")
    if outcome == "succeeded" or closure in {"ready_for_review", "closed"}:
        if not criteria or any(not isinstance(c, dict) or c.get("status") not in {"passed", "not_applicable"} for c in criteria):
            issues.append("lifecycle_completion_overstated")
        if not any(isinstance(c, dict) and c.get("status") == "passed" for c in criteria):
            issues.append("lifecycle_completion_without_evidence")
    if closure in {"ready_for_review", "closed"} and outcome != "succeeded":
        issues.append("lifecycle_closure_outcome_mismatch")
    if closure == "cancelled" and outcome != "cancelled":
        issues.append("lifecycle_cancellation_outcome_mismatch")
    required_axes = value.get("required_axes")
    axes = {"implementation", "verification", "external_integration", "delivery", "deployment", "human_acceptance"}
    if (not isinstance(required_axes, list) or not required_axes
            or any(not isinstance(a, str) or a not in axes for a in required_axes)):
        issues.append("lifecycle_required_axes_invalid")
        required_axes = []
    states = task.get("states") if isinstance(task.get("states"), dict) else {}
    if outcome == "succeeded" and any(states.get(axis) != "passed" for axis in required_axes):
        issues.append("lifecycle_required_axis_incomplete")
    if type(value.get("human_acceptance_required")) is not bool:
        issues.append("lifecycle_acceptance_policy_missing")
    if closure == "closed":
        if not value.get("closure_ref"):
            issues.append("lifecycle_closure_receipt_missing")
        if value.get("human_acceptance_required") and states.get("human_acceptance") != "passed":
            issues.append("lifecycle_human_acceptance_missing")
    resources = value.get("resources")
    if not isinstance(resources, list):
        issues.append("lifecycle_resources_invalid")
        resources = []
    cleanup = value.get("resource_cleanup_status")
    if cleanup not in {"pending", "partial", "passed", "failed", "not_applicable"}:
        issues.append("lifecycle_cleanup_state_invalid")
    if cleanup == "not_applicable" and resources:
        issues.append("lifecycle_resources_not_applicable")
    resource_keys: set[str] = set()
    for resource in resources:
        if not isinstance(resource, dict):
            issues.append("lifecycle_resource_invalid")
            continue
        key = resource.get("key")
        if not isinstance(key, str) or not key or key in resource_keys:
            issues.append("lifecycle_resource_identity_invalid")
        else:
            resource_keys.add(key)
        ownership, state = resource.get("ownership"), resource.get("state")
        if ownership not in {"created", "borrowed", "shared"} or state not in RESOURCE_STATES:
            issues.append("lifecycle_resource_state_invalid")
        if resource.get("holder_run_ref") != run:
            issues.append("lifecycle_resource_run_mismatch")
        if resource.get("kind") not in {"browser_tab", "process", "service", "connection", "lock", "worktree", "file", "debug_setting"}:
            issues.append("lifecycle_resource_kind_invalid")
        action = resource.get("action")
        if action not in {"none", "release_control", "close", "stop", "release", "retain", "restore"}:
            issues.append("lifecycle_resource_action_invalid")
        change = resource.get("temporary_change")
        owned_change = (resource.get("kind") == "debug_setting" and action == "restore"
                        and isinstance(change, dict) and change.get("owner_run_ref") == run
                        and all(SHA256.fullmatch(str(change.get(field, ""))) for field in ("before_hash", "applied_hash"))
                        and nonempty(change.get("authorization_ref")))
        if ownership != "created" and action in {"close", "stop", "release", "restore"} and not owned_change:
            issues.append("lifecycle_borrowed_resource_destructive_action")
        if action == "restore" and not owned_change:
            issues.append("lifecycle_setting_change_unproven")
        allowed_actions = {
            "browser_tab": {"none", "retain", "close", "release_control"},
            "process": {"none", "retain", "stop"}, "service": {"none", "retain", "stop"},
            "connection": {"none", "retain", "release"}, "lock": {"none", "retain", "release"},
            "worktree": {"none", "retain", "release"}, "file": {"none", "retain", "release"},
            "debug_setting": {"none", "retain", "restore"},
        }
        if action not in allowed_actions.get(resource.get("kind"), set()):
            issues.append("lifecycle_resource_action_kind_mismatch")
        receipt = resource.get("receipt")
        bound_receipt = (isinstance(receipt, dict) and receipt.get("resource_key") == key
                         and receipt.get("action") == action and receipt_valid(receipt, run))
        if state == "released" and not bound_receipt:
            issues.append("lifecycle_resource_receipt_invalid")
        if state == "released" and action in {"none", "retain"}:
            issues.append("lifecycle_resource_release_action_missing")
        if state == "released" and owned_change and (not isinstance(receipt, dict) or receipt.get("restored_hash") != change["before_hash"]):
            issues.append("lifecycle_setting_restore_unverified")
        if state == "retained":
            retention = resource.get("retention")
            if not isinstance(retention, dict) or any(not isinstance(retention.get(f), str) or not retention[f].strip() for f in ("purpose", "owner", "review_condition")):
                issues.append("lifecycle_resource_retention_missing")
            if action not in {"retain", "none"}:
                issues.append("lifecycle_resource_retention_action_invalid")
        control = resource.get("control_state")
        if resource.get("kind") == "browser_tab":
            if ownership == "created" and action == "release_control" and state == "released":
                issues.append("lifecycle_created_page_disposition_missing")
            control_declaration = resource.get("control")
            if "control" in resource:
                if not isinstance(control_declaration, dict):
                    issues.append("lifecycle_browser_control_invalid")
                    control_declaration = {}
                if "control_state" in resource and control != control_declaration.get("state"):
                    issues.append("lifecycle_browser_control_conflict")
                control = control_declaration.get("state")
                mode = control_declaration.get("release_mode")
                if mode not in {"explicit", "automatic", "unsupported"}:
                    issues.append("lifecycle_browser_capability_missing")
                control_receipt = control_declaration.get("receipt")
                control_action = control_declaration.get("action")
                if control_action not in {"release_control", "close"}:
                    issues.append("lifecycle_browser_control_invalid")
                control_bound = (control_action in {"release_control", "close"}
                                 and isinstance(control_receipt, dict)
                                 and control_receipt.get("resource_key") == key
                                 and control_receipt.get("action") == control_action
                                 and receipt_valid(control_receipt, run))
                if control_action == "close" and (action != "close" or state != "released"):
                    control_bound = False
                if mode == "unsupported" and control == "released":
                    control_bound = False
            else:
                # Legacy closed-tab receipts still work. A retain receipt has
                # never been evidence that the separate control lease ended.
                control_bound = bound_receipt and action in {"close", "release_control"}
            if control not in {"held", "released", "pending_automatic", "unsupported", "unknown"}:
                issues.append("lifecycle_browser_control_invalid")
            if control == "released" and not control_bound:
                issues.append("lifecycle_browser_control_receipt_invalid")
            if cleanup == "passed" and control != "released":
                issues.append("lifecycle_browser_release_unverified")
        if cleanup == "passed" and state not in {"released", "retained"}:
            issues.append("lifecycle_cleanup_overstated")
        if stage == "ended" and state == "active":
            issues.append("lifecycle_ended_resource_active")
    if stage == "ended" and not value.get("next_action"):
        issues.append("lifecycle_next_action_missing")
    return sorted(set(issues))
