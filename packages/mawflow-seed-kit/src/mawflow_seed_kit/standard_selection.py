"""Explainable tri-state selection over the existing standards catalog."""
from __future__ import annotations

from typing import Any

FACTS = {"source_change", "project_setup", "requirements_change", "public_contract",
         "external_dependency", "browser", "database", "resources", "knowledge_reuse"}


def validate_applicability(value: Any) -> bool:
    if not isinstance(value, dict) or not value or set(value) - {"any_facts", "all_facts"}:
        return False
    for names in value.values():
        if (not isinstance(names, list) or not names
                or any(not isinstance(name, str) or name not in FACTS for name in names)
                or len(names) != len(set(names))):
            return False
    return True


def validate_facts(facts: Any) -> dict[str, bool]:
    if (not isinstance(facts, dict) or set(facts) - FACTS
            or any(type(value) is not bool for value in facts.values())):
        raise ValueError("selection_facts_invalid")
    return facts


def select_rules(rules: list[dict], phase: str, task_class: str, task_kind: str,
                 facts: dict[str, bool] | None = None) -> tuple[list[dict], list[dict]]:
    facts = validate_facts({} if facts is None else facts)
    selected, excluded = [], []
    for rule in rules:
        if ((phase and phase not in rule["applies_to_phases"])
                or task_class not in rule["task_classes"] or task_kind not in rule["task_kinds"]):
            excluded.append({"key": rule["key"], "reason": "outside_phase_class_or_kind"})
            continue
        condition = rule.get("applicability", {})
        outcomes: list[bool | None] = []
        missing: set[str] = set()
        for operator, names in condition.items():
            values = [facts.get(name) for name in names]
            if operator == "any_facts":
                outcome = True if True in values else (None if None in values else False)
            else:
                outcome = False if False in values else (None if None in values else True)
            outcomes.append(outcome)
            if outcome is None:
                missing.update(name for name in names if name not in facts)
        if False in outcomes:
            excluded.append({"key": rule["key"], "reason": "explicit_facts_not_applicable"})
            continue
        pending = None in outcomes
        selected.append({**rule, "selection": {
            "status": "pending_applicability" if pending else "applicable",
            "reason": "missing_facts" if pending else ("facts_matched" if condition else "phase_class_kind_matched"),
            "missing_facts": sorted(missing),
        }})
    return selected, excluded
