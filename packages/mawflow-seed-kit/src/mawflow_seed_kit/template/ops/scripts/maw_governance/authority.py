"""Deterministic business revisions and reading documents from source records."""
from __future__ import annotations

from collections import defaultdict, deque


def resolve_business(items: list[dict]) -> None:
    by_id = defaultdict(list)
    groups = defaultdict(list)
    for item in items:
        by_id[item["id"]].append(item)
        if item.get("business"):
            groups[(item["business"]["key"], item["business"]["scope"])].append(item)
    for group_key, group in groups.items():
        nodes = {i["id"]: i for i in group}
        parents, children, invalid = {}, defaultdict(list), set()
        for item in group:
            ref = item["id"]
            item.update(business_status="proposal", business_issues=[], previous=[], open_proposals=0)
            refs = ([item["supersedes"]] if item["supersedes"] else []) + item["resolves"]
            parents[ref] = []
            if len(by_id[ref]) != 1 or len(set(refs)) != len(refs):
                invalid.add(ref)
            for old in refs:
                candidates = by_id.get(old, [])
                if len(candidates) != 1 or old == ref:
                    invalid.add(ref)
                    continue
                previous = candidates[0]
                business = previous.get("business")
                if business and (business["key"], business["scope"]) != group_key:
                    invalid.add(ref)
                    continue
                if not business and (item["resolves"] or previous["lifecycle"] == "conflict"):
                    invalid.add(ref)
                    continue
                item["previous"].append({k: previous[k] for k in ("id", "statement", "decision_status", "source_path")})
                if business:
                    parents[ref].append(old)
                    children[old].append(ref)
            if item["business"]["effect"] == "retire" and not refs:
                invalid.add(ref)

        # Iterative topological traversal also quarantines cycles and downstream
        # dependants without recursion or timestamp-based authority decisions.
        degree = {ref: len(refs) for ref, refs in parents.items()}
        queue = deque(ref for ref, n in degree.items() if n == 0)
        order = []
        while queue:
            ref = queue.popleft()
            order.append(ref)
            for child in children[ref]:
                if ref in invalid:
                    invalid.add(child)
                degree[child] -= 1
                if degree[child] == 0:
                    queue.append(child)
        invalid.update(set(nodes) - set(order))
        confirmed_descendants, any_descendants = set(), set()
        for ref in reversed(order):
            if ref in invalid:
                continue
            for parent in parents[ref]:
                any_descendants.add(parent)
                if nodes[ref]["decision_status"] == "confirmed" or ref in confirmed_descendants:
                    confirmed_descendants.add(parent)

        heads = []
        for item in group:
            ref = item["id"]
            if ref in invalid:
                item.update(business_status="conflict", lifecycle="conflict", business_issues=["invalid_revision_chain"])
                if item["decision_status"] == "confirmed":
                    heads.append(item)
            elif item["decision_status"] == "confirmed":
                if ref in confirmed_descendants:
                    item.update(business_status="history", lifecycle="superseded")
                else:
                    heads.append(item)
            elif item["decision_status"] == "rejected" or ref in any_descendants:
                item.update(business_status="history", lifecycle="superseded")
            for child in children[ref]:
                item["superseded_by"].append(child)
        for item in heads:
            if len(heads) > 1:
                item.update(business_status="conflict", lifecycle="conflict")
                item["business_issues"].append("multiple_confirmed_versions")
            elif item["id"] not in invalid:
                # A normative requirement remains authoritative when implementation
                # evidence evolves. Facts need revalidation; damaged joint records
                # never activate an answer independently of their fixed document.
                fact_dependent = (item.get("qa") or {}).get("claim_type") != "requirement"
                invalid_basis = item.get("artifact_integrity", "current") != "current" or (fact_dependent and item["freshness"] != "current")
                item["business_status"] = ("source_changed" if invalid_basis else
                                           "retired" if item["business"]["effect"] == "retire" else "current")
        proposals = sum(i["business_status"] == "proposal" for i in group)
        for item in group:
            item["open_proposals"] = proposals
            # A confirmed v2 definition can explicitly classify an old v1 source.
            if item["decision_status"] == "confirmed" and item["id"] not in invalid:
                for previous in item["previous"]:
                    old = by_id[previous["id"]][0]
                    if not old.get("business"):
                        old["lifecycle"] = "superseded"
                        old["superseded_by"].append(item["id"])
