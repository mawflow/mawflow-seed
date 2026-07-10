# 中文人类优先收口模板

## 结论

<一句话说明任务完成状态、是否阻塞、是否需要用户确认。>

## 变更

- <关键变更 1>
- <关键变更 2>

## 验证

<通过/未通过/部分通过。用一句话说明覆盖范围、未覆盖项和风险；默认不要列命令清单。>

<用户要求详细收口、展开验证，或验证失败/warning/未运行时，使用下面明细；否则删除。>

- `<命令>`：<结果>
- 未运行：<原因，如无则删除本行>

## Git/镜像

- 提交：<已提交/未提交及原因>
- 推送：<已推送/未推送及原因>
- 仓库级 mirror：<已同步/按开关跳过/未执行及原因>

## 模块与记忆

- 模块档案：<已更新/未更新及原因>
- 待办任务：<新增/完成/取消/查询了哪些 TODO-ID，或未涉及被依赖但暂不实现的待办任务>
- 项目健康上下文：<新增/更新/审计/未涉及哪些 .maw/health 记录 ID，或说明无需更新>
- 技术地图/公共能力：<新增/复用/废弃/未涉及哪些 capability_key，或说明无需更新>
- 项目信号：<新增/更新/关闭/未涉及哪些 signal_id，或说明无需更新>
- 仓库身份：<新增/更新/判断/未涉及 declared roles、detected roles、角色目录覆盖和高风险约束>
- 项目指令/经验：<已更新/未更新及原因>
- 本机 local：<已更新/未更新及原因>
- 用户口径：<已沿用/本次确认并沉淀/未涉及>

## 种子仓库升级建议

<说明本轮是否发现可回流到种子仓库 maw-project-template 的优化或新增能力。有则写候选记录位置、使用场景、理由、是否已生成种子仓库执行提示词和向下兼容要求；没有则写“未发现新的种子仓库升级建议”。>

## 发布影响

- 命中 code 组件：<app_key 列表或“无”>
- 发布状态：<无需发布/需要发布但未发布/已发布并验证>
- 发布版本：<如执行或计划发布，说明目标环境、候选 commit、已发布 commit/状态文件、纳入或跳过组件；上线/生产说明本地最新检查>
- 发布指令：<需要时列出可复制 #发布 指令>

## code 交付影响

<说明是否影响 code-only 交付、是否需要重新导出或重新检查。>

## 需要你补充

<没有需要用户补充的参数、问题或确认时删除本节。需要时按下面格式填写 1 到 3 项。>

- 参数/问题：<必填/可选，说明要提供什么>
  用途与影响：<这个值影响哪一步，选错有什么风险>
  获取步骤：<具体从哪个文件、命令、系统页面或负责人处获取>
  建议选项：<推荐选项；其它可选项及一句话取舍>
  本机填写文件：<如涉及敏感参数，先创建并填写 .local/...；非敏感参数可删除本行>
  填写格式：<示例；敏感值用 secret 引用、本机配置路径、环境变量名或“已完成配置”，不要在对话里贴明文>

## 下一步

<仅在用户需要继续操作时填写可复制命令或确认语句。>

## 技术元数据

<默认只保留本轮有实际信息量或任务包硬性要求的字段；用户要求详细收口、审计版或机器可读交接时，再输出完整字段清单。>

```text
experience_lookup:
module_key:
module_candidate:
module_dossier_updated:
module_dossier_reason:
updated_module_docs:
hit_code_components:
modified_components:
release_update_status:
release_commands:
release_confirmation_prompt:
local_environment_status:
local_test_entry:
local_update_commands:
local_environment_install_hint:
code_delivery_status:
todo_task_update_status:
health_context_update_status:
capability_map_update_status:
project_signal_update_status:
repository_identity_update_status:
mcp_diagnostics_instruction:
host_purpose_mcp_alignment:
capability_credential_variable_alignment:
memory_update:
local_update:
upgrade_strategy_update:
seed_repository_upgrade_suggestions:
user_terms_style:
```
