---
doc_key: docs.capabilities.local-directory-canonicalization
doc_type: governance
stage: governance
status: active
owner: planner
tags:
  - local
  - configuration
  - security
read_contract:
  summary: "本机配置、引用与运行状态统一进入 .local 的机器和人工治理契约。"
  ai_read_hint: "新增本机文件、迁移旧 .maw/*.local.*、导出公开 Seed 或设计本机状态路径时读取。"
---

# 本机文件 `.local` 规范目录

## 规范路径

- 配置 overlay：`.local/.maw/<domain>.yaml` 与 `.local/.maw/<domain>.d/*.yaml`。
- 本机运行状态：`.local/maw/`。
- 其它本机辅助配置：`.local/config/`、`.local/ai/`、`.local/maintenance/`。
- 项目凭证 binding：`.local/.maw/project.yaml`，只保存受控引用和非敏感元数据。

旧 `.maw/<domain>.local.yaml` 和 `.maw/<domain>.local.d/*.yaml` 只保留读取兼容性。任何 UI、CLI、脚本或新项目模板都不得再把它们作为新写入目标。

## 安全与迁移边界

- `.local/**` 默认 Git ignore；模板和公开 Seed 只允许跟踪 README 与 `*.example.yaml`。
- 真实 Token、密码、私钥、连接串、内部 remote、本机路径和运行状态不得进入提交、日志、诊断包或公开 payload。
- 检测到旧 local 文件时只能报告路径和迁移计划；未经用户确认，不读取内容、不复制、不移动、不删除。
- 迁移时只合并 ref 和非敏感配置，完成专项验证后再由用户决定是否清理旧文件。

## 读取优先级

共享 `.maw` 层先加载，旧 `.maw/*.local.*` 兼容层随后加载，规范 `.local/.maw` 层最后加载并获最高优先级。关闭本机差异的发布、交付和审计流程应使用 `--no-local`。

## 验证

```bash
python3 -m pytest -q tests/test_maw_config_loader.py tests/test_public_seed_workdir.py
bash ops/scripts/check-local-boundary.sh
bash ops/scripts/check-seed-open-source-readiness.sh --strict
```
