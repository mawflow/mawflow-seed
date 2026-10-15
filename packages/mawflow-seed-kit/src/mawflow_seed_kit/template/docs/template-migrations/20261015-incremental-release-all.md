# 发布全部与逐组件成功基线

## 采用范围

用户提出Seed增加发布全部指令，并按每个组件上次成功发布的Git提交筛选。本次沿用TINST-014、现有部署目标、外部代码源解析和发布状态目录；新增 `#发布全部` / `--all` 入口，多组件实际成功名单显式记录。

源码开发完成，尚未公共Seed/Kit发行、主仓模板升级或任何真实应用发布。无业务组件和正式模块档案；本项为Seed发布治理能力 `incremental-release-all`，不创建业务leaf。

## 增量取舍

| 路径/事实 | 处理 |
| --- | --- |
| `ops/scripts/plan-release-components.py` | 合并发布全部、成功组件限制、状态原子替换及dirty/范围变化判断；已有项目保留自定义适配 |
| `docs/ai-instructions/instructions/release-component.md`、命令索引 | 增加入口及正确成功记录约束，保留TINST-014与已有环境口径 |
| `.maw/releases.yaml` | 只合并说明/缺失能力；保留真实环境、组件、共享路径和目标配置 |
| `artifacts/release-state/**` | 保留目标项目自己的历史，只读兼容旧路径/字段；不导入Seed状态 |
| Kit物化 | 同时携带规划脚本、配置读取器、配置及说明；默认空组件、空部署范围保持 |

“全部”不跨环境或自动选择多个服务器。多个部署目标须明确选择；没有部署范围时继续拒绝。通过实际组件发布脚本执行构建、部署与验证，规划命令不执行远端操作。每个成功状态绑定环境、目标、组件和完整提交；未发布或失败者保留旧状态；单纯跳过不能把状态推进到当前HEAD。

## 验证入口

```bash
python3 -m pytest -q tests/test_plan_release_deployment_targets.py
python3 -m py_compile ops/scripts/plan-release-components.py
bash ops/scripts/check-template-module-docs.sh
bash ops/scripts/check-ai-framework-consistency.sh
bash ops/scripts/check-local-boundary.sh
```

专项使用临时Git仓库和模拟成功声明，覆盖完整/部分成功、无变化跳过、共享路径和部署范围变化、dirty前后、损坏/未验证状态、提交倒退、环境默认与作用域、Git/Kit物化运行；不代表真实环境部署或真人验收。完整测试结果以本轮来源收录回执为准。

`module_dossier_updated: not_required`（Seed无业务模块，能力与指令文档已同步）；`hit_code_components: none`；无需业务发布或Host重启。`capability_map_update_status: added incremental-release-all`；`repository_identity_update_status: unchanged`；`health_context_update_status: not_required`；长期采用边界记入能力说明和候选台账，不新增重复任务账本。主仓与其它派生项目分别经模板升级采用，公共发行独立执行。


## 本轮验证结果

- 发布规划专项18项通过，包含Kit物化后的实际脚本运行；便携CLI与治理专项22项通过，合计40项。
- 使用当前源码包的 `PYTHONPATH=packages/mawflow-seed-kit/src` 验证；全局已安装Kit不代表本轮已采用。
- 模板协议、技术地图、仓库身份、宿主机用途/MCP、AI框架、本机边界及差异空白检查通过；Python编译通过。
- 开发资源检查warning，重任务串行；共享Agent上下文已通过CLI回读。本轮无新增服务或部署，没有数据库写入。
- 来源事件与更新动态按本轮规范追加。公共发行、真实多设备采用、应用发布验证和真人验收未执行。

## 会话收口补充

同步 `.maw/interaction.yaml`、Agent 收口入口、TINST-020、工作流、编码规范与模块收口模板，统一引用 `docs/ai-coding/release-closeout.md`。Kit 的轻量 Agent 入口和 TINST-014 同样引用规范。已有项目增量合并，保留项目原有语言、组件、默认环境与部署配置；未采用规划器的项目仍使用原有单组件指令，不得假定已支持 `--all`。

收口展示上次成功发布提交、本次候选提交、逐组件状态和具体确认范围；新增规则与物化入口通过本轮治理检查，未执行真实部署或公共发行。
