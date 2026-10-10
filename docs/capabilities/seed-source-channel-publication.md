---
doc_key: docs.capabilities.seed-source-channel-publication
doc_type: capability
stage: governance
status: active
owner: planner
tags:
  - seed
  - template-upgrade
  - open-source
  - repository-publish
project_health:
  dimensions:
    - ai_collaboration
    - delivery
  evidence_level: canonical
read_contract:
  summary: "Seed 来源通道与公开发布协议说明。"
  health_signal: "用于模板漂移升级、公开 Seed 分发和私有开发仓发布到公开仓前的来源通道判断。"
  consumes:
    - .maw/template-source.yaml
    - .maw/repositories.yaml
  produces:
    - docs/template-migrations/
    - prompts/codex/template-upgrade-prompts/
  ai_read_hint: "处理 #模板升级、#模版升级、Seed 来源通道或 #发布公开镜像 前读取。"
---

# Seed 来源通道与公开发布协议

该能力统一两类派生项目的升级来源：

- 平台主仓：经共享项目身份、仓库角色与 Git origin 校验，从登记并绑定的独立 Seed Git 目录读取已提交的固定 commit，允许先验证尚未公开的候选；目录缺失、来源不匹配或工作区脏时只阻断模板升级，不回退。
- 其它所有派生项目（含内部开发仓）：使用 `public_seed`，默认解析 `latest_verified_stable` 或指定稳定 tag；回读公开 tag、Payload Manifest、Seed lock 与同版本 Kit checksum/manifest，不采用 main、rc、任意 commit、私有源或本机目录覆盖。
- 历史未知或内部来源项目：保留旧来源与基线，通过版本、契约和公开载荷证据预览来源迁移；不直接换 URL 或沿用不属于公开历史的 SHA。

脚本与 CLI 的唯一实现为 Seed Kit `commands/template_drift.py` 和 `commands/template_policy.py`（>=2.12.0）。当前公共稳定版本以公开 tag/manifest/Kit 的成功回读为准，主仓发布事实由 `.maw/seed-distribution.yaml` 维护，本文不维护版本副本。

公开发布使用通用 `#发布公开镜像` / `repository_publish_mirrors` 协议。模板仓只定义默认关闭的结构、gate 和脱敏导出模式，不写主仓真实 target、token、本机 remote、发布记录目录或主仓专用 `#发布Seed开源仓` 指令。

默认发布模式优先使用 `export_sanitized_tree`。只有人工确认私有 Git 历史完全适合公开时，才改用 `same_git_history`。

验证入口：

```bash
bash ops/scripts/check-template-module-docs.sh
bash ops/scripts/check-technical-map.sh
bash ops/scripts/check-local-boundary.sh
```

## 模板与契约升级验收（2026-09-07）

`plan-template-drift.py` 分别检查模板提交和 Seed Contract。模板与契约同时落后时，当前会话提示词必须包含受控契约迁移；仅推进 `applied_version` 后仍会返回 `seed_contract_behind`，直至契约回读通过。缺少历史基线只初始化本次采用目标，不追溯历史，也不免除契约迁移。

源 `.maw/seed.lock` 缺失、无法解析或版本/契约/指纹不完整时返回 `seed_contract_unavailable`，`template_status` 保留提交关系，禁止宣称已对齐。模板 `ahead/diverged` 仍保留原停止规则，较新的项目契约不得回退。工作台以本机 Seed Kit 为比较目标，必须与源模板对齐结论分别报告。

验证：`python3 -m pytest -q tests/test_plan_template_drift.py` 覆盖双漂移、只推进模板基线、契约缺失/损坏、缺失历史基线和较新版本保护。修复属于升级计划及指令，不会自动迁移业务项目、更新 Host 或发布公开 Seed。
