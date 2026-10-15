# 可选运行健康增量支持

本次是 2.14 开发候选的附加协议资产，不提升公共稳定版本，不改变 Contract v2 必需字段或目标项目 applied_version。平台运行服务不进入 Seed。

升级前核对目标现有运行健康、原生接口和项目边界；只增量合并对应 schema、示例、文档与离线检查脚本。已有 `.maw/runtime-health.json`、业务代码、项目 README、组件 app_key、生产配置、模板来源锁、本机绑定及凭据全部保留。不要以模板升级为由启用组件或探测生产。

- 不需要巡检的项目：不创建实际声明，检查结果为 `not_adopted`，成功且零写入。
- 明确关闭：采用仅含 schema 和 `enabled:false` 的声明，结果为 `disabled`。
- 已有原生能力：由业务实现任务提供标准只读 GET 投影，复用现有权限、租户、缓存和环境识别；无需部署另一套采集器。
- 需要通用采集：另行按项目授权选择并部署组件，地址与凭据留在环境绑定里；声明中的检查不执行任意命令。

使用 [协议说明](../capabilities/runtime-health-contract.md) 和 `python3 ops/scripts/check-runtime-health.py --root . --format json` 离线验证。再按独立任务验证原生端点/采集服务、身份绑定、鉴权、过期、故障恢复和工作台；离线检查通过不能标为目标环境健康。

回退时仅撤销本次新增的协议资产或关闭项目声明；不得删除原生健康能力、目标数据或已有绑定。正式公共分发和其它派生项目采用继续走各自受控流程，本次未触发。

## 本地验证回执

2026-10-15：13项声明与Git/Kit物化测试通过。新项目没有启用声明或采集服务；未采用与关闭零写入，原生与独立采集示例均通过，命令/URL/写方法/重复键/非法路径/非有限数/敏感扩展字段拒绝。模板文档、AI框架、本机边界和技术地图检查通过。未发布公共Seed，未自动升级其它派生项目或提升模板来源锁。

module_dossier_updated=false：本仓仅新增通用协议，无业务模块；capability_map_update_status=updated；project_signal_update_status=not_needed；repository_identity_update_status=unchanged；health_context_update_status=unchanged；release_update_status=not_released；local_update=not_applied；memory_update=project_docs。
