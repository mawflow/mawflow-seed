# 可选择本地调试与 Seed 脚本合同

- 日期：2026-09-04
- 风险等级：T3
- 适用范围：需要让本地工作台可视化管理并执行 Seed 脚本，或现有 `npm run dev` 会无差别启动全部应用的派生项目。

## 目标

Seed 只规定稳定脚本入口和用途分类，不替每个项目发明真实业务命令。`npm run dev` 继续是规范入口，`npm run local:dev` 读取当前设备选择，调用组件描述或组件 `package.json` 已有的 `dev/start`。项目工作台读取、解释并受控执行同一份声明，不再维护第二套启动配置。

## 增量迁移

1. 先只读盘点根 `package.json`、`.maw/app-runtime.yaml`、`.maw/components.yaml`、各组件 `.maw.component.yaml` / `package.json` 和现有 `ops/scripts`。
2. 把现有真实启动方式归到对应应用的 `commands.dev` / `commands.start` 或组件脚本。若旧 `local:dev` 承载业务聚合命令，必须保留其行为或迁入组件后再改线，不得直接覆盖。
3. 增量加入 `ops/scripts/run-local-dev.py` 和薄包装 `ops/scripts/local-dev.sh`；让 `dev` 转发 `local:dev`，补充 `dev:list`、`dev:status`、`dev:stop` 和人类可读脚本说明。
4. 在 `.maw/app-runtime.yaml` 只保存团队默认 preset。当前设备的 preset / app keys 由本地工作台写入 Git 已忽略的 `.local/.maw/app-runtime.yaml`；运行 PID、日志和状态进入 `.local/run/local-dev/`。
5. 用 `npm run dev:list` 核对范围，再执行一次 `npm run dev` 或工作台“后台启动并复检”。只有当前范围真实启动成功，才把本地调试阻塞标记为完成。

## 工作台口径

- 默认提供“项目默认应用”“前端 + 后端联调”“全部可运行服务”，并允许当前设备逐项选择。
- 未选应用继续展示，但不启动、不探测、不阻塞。
- 本地调试结论只看选择、真实命令、规范入口和一次成功启动；工具链、依赖、编译、发布是其它 Seed 规范项。
- 启动是持久后台任务，必须先预览和确认，并提供真实阶段、脱敏日志、取消和失败重试。发布、部署、数据库脚本仍在所属流程执行。

## 保护边界

迁移只做语义增量合并，不覆盖 README、`code/`、真实 app_key、已有业务脚本语义、发布配置、仓库映射、secrets、`.local/` 内容或模块档案。`.maw/**` 是 Git 共享声明；`.local/**` 是当前设备本地化工作目录，不能反向成为团队默认。
