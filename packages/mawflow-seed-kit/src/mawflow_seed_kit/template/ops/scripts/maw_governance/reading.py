"""Deterministic human reading and reference impact over the effective answers."""
from collections import defaultdict

from .store import digest


PARTITIONS = {"business": "业务问答", "technical": "技术约定", "environment": "环境与阶段", "experience": "项目经验"}


def reading(snapshot: dict, scope: str = "", module: str = "") -> dict:
    organizations = {}
    for item in sorted(snapshot["items"], key=lambda i: (i["captured_at"], i["id"])):
        organization = item.get("organization")
        if organization:
            organizations[(organization["question_key"], organization["scope"])] = organization
    groups = defaultdict(list)
    for question in snapshot["questions"]:
        if scope and question["scope"] not in {"project", scope}:
            continue
        organization = organizations.get((question["question_key"], question["scope"]), {})
        for item in question["current"]:
            if item["business_status"] == "retired" or (module and item.get("modules") and module not in item["modules"]):
                continue
            category = question["category"]
            chapter = organization.get("chapter") or (item.get("modules") or ["项目通用"])[0]
            groups[(category, chapter)].append({"question_key": question["question_key"], "scope": question["scope"],
                "question": item["business"]["title"], "answer": item["statement"], "ref": item["id"],
                "source_hash": item["source_hash"], "status": item["business_status"], "claim_type": (item.get("qa") or {}).get("claim_type", "requirement"),
                "rationale": (item.get("qa") or {}).get("rationale", ""), "exceptions": (item.get("qa") or {}).get("exceptions", []),
                "confirmation": item.get("confirmation"), "freshness": item["freshness"], "source_path": item["source_path"],
                "order": organization.get("order", 0), "modules": item.get("modules", [])})
    chapters = []
    refs = []
    for (category, title), questions in sorted(groups.items(), key=lambda pair: (list(PARTITIONS).index(pair[0][0]) if pair[0][0] in PARTITIONS else 99, pair[0][1])):
        questions.sort(key=lambda q: (q["order"], q["question"], q["ref"]))
        for index, question in enumerate(questions, 1):
            question["number"] = index
            refs.append(question["ref"])
        chapters.append({"key": digest([category, title])[:16], "title": title, "category": category,
                         "category_label": PARTITIONS.get(category, "待整理"), "questions": questions})
    content = {"project_key": snapshot["project_key"], "scope": scope, "module": module, "chapters": chapters}
    return {"schema": "mawflow.governance_reading.v1", **content, "input_hash": digest(content),
            "question_refs": sorted(refs), "source_version": snapshot["source_version"],
            "partial": snapshot["partial"], "issues": snapshot["issues"], "total": len(refs)}


def render_reading(view: dict) -> str:
    lines = ["# 项目口径", "", "以下正文来自精确版本的有效口径；待确认候选不会替代当前规则。", ""]
    for chapter in view["chapters"]:
        lines += [f"## {chapter['category_label']} · {chapter['title']}", ""]
        for question in chapter["questions"]:
            lines += [f"### Q{question['number']} {question['question']}", "", question["answer"], ""]
            if question["exceptions"]:
                lines += ["适用条件与例外：", "", *[f"- {value}" for value in question["exceptions"]], ""]
            lines += [f"性质：{question['claim_type']}；状态：{question['status']}；依据：`{question['ref']}`。", ""]
    if view["partial"]:
        lines += ["部分来源不可读，请核对来源问题；此页不能证明全量覆盖。", ""]
    return "\n".join(lines)


def impacts(snapshot: dict, refs: list[str]) -> dict:
    selected = set(refs)
    return {"artifacts": [i["id"] for i in snapshot["artifacts"] if selected.intersection(i["artifact"]["question_refs"])],
            "consumptions": [i["id"] for i in snapshot["consumptions"] if selected.intersection(i["consumption"]["question_refs"])],
            "baselines": [i["id"] for i in snapshot["items"] if selected.intersection((i.get("baseline") or {}).get("question_refs", []))],
            "effect": "后续有效阅读和AI上下文使用新版本；历史任务、档案和基线保持原版本引用。"}
