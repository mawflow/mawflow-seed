---
doc_key: governance.cli-p2
doc_type: governance
stage: development
status: active
owner: seed-maintainer
tags: [cli, governance, p2]
read_contract:
  summary: Seed CLI P2 公共呈现契约。
  ai_read_hint: 按当前任务查看源码候选范围；不代表已公开发行或本机正式采用。
---

# Seed CLI P2 候选契约

2026-10-15 在已有 P1 基线上继续治理。Seed 只维护通用 CLI 输出契约与项目 Doctor 摘要；Host、npm、账号、Shell 会话及本机 preflight 留在平台主仓。没有发布、安装、推进项目采用基线或覆盖其它任务改动。

- `version`、`--version` 与 `profile` 返回 `mawflow.cli_runtime.v1`：Seed 源码版本来自 catalog，安装 metadata 单列；Host/facade 通过显式参数补自己的源码版本，npm 传入实际已选 profile 和启动器版本。Python 直连标记 `python_entrypoint`。版本号不等于已包含开发候选修复，安装事实须独立核验。
- `cli_contract.py` 提供解析器、无折行 JSON version action、错误输出和边界异常处理。正常结果或有效预览为 0，领域阻断为 1，解析/工作目录参数错误为 2；解析错误 JSON 写 stderr，不回显可能含敏感值的 argv。保留旧 `error` 并增加 `error_code`、`exit_code`。SSH 远程会话退出码和中断由平台入口另行处理。
- 公共来源策略失败的漂移计划为退出码 1；有效漂移预览沿用 Seed 原有允许状态。公开稳定 tag、payload manifest、Kit wheel 哈希仍必须核验，本地 URL 不获得例外。
- `project doctor` 默认省略 `project`、`configs`、`local_configs` 和原始错误 message。保留兼容性、总计、最多各 50 条问题/失败来源及截断数量，按稳定字段排序；详细编译 API `compile_project_definition` / `project_doctor` 不变。需要更多上下文时使用有界 `project context`，不把本机覆盖正文当公开诊断输出。

这是未发行的源码契约。P2 实现时沿用名义版本 2.13.0；后续发行准备已分配 2.14.0，见 [发行准备](cli-governance-release-preparation.md)。已公开的 2.13.0 制品不含本轮新增 API。后续发行必须先给新不可变 Kit/facade/Host 分配版本、冻结 consumer 的精确依赖并验证真实 wheel，不能覆盖已有 2.13.0 或以本轮源码测试声称公开包可用。本轮不执行发行准备写入。

验证入口：`tests/test_cli_contract.py`、`tests/test_cli_governance.py`、`tests/test_portable_cli.py`、`tests/test_template_source_policy.py`、`tests/test_plan_template_drift.py`。平台双入口、只读审计钩子、Host Doctor 和 preflight 由主仓独立验收。

本轮验证：上述 7 组 suite 共 142 passed；版本对齐、模板模块、AI 框架与本机边界检查通过。平台联合 192 项、最终入口专项 29 项及 npm 30 项由主仓回执记录，互有重叠，不相加。主仓与 Seed 分别提交 dev；未公开发行、未安装、未做真人验收。
