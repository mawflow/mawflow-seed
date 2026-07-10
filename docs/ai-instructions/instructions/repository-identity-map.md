# 指令：仓库身份地图

## 元信息

- ID：TINST-031
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/repository-identity-map.md`
- 推荐调用：`#仓库身份`
- 精确调用：`#T031` 或 `#T031/仓库身份`
- 触发词：#仓库身份、仓库身份、身份地图、仓库角色、多角色、角色目录、种子仓、主仓、平台项目仓、客户项目仓、混合仓、unknown_legacy、repository identity、repository role
- 适用范围：判断当前仓库是种子仓、主仓、平台项目仓、客户项目仓、混合仓或历史未分类仓；在模板升级、客户同步、MCP、发布、密钥、外部交付或 code-only 导出前确认差异化边界。

## 目标

让人和 AI 在进入仓库时先知道“我是谁、能看什么、能写什么、不能做什么”。仓库身份地图把仓库角色、关联仓关系、可见/可写面、受保护事实和差异化约束接口沉淀为结构化元数据，供新会话、巡检、大屏和 MCP 诊断使用。仓库可以是多角色；项目按 `current_repository.roles` 吃到对应角色目录下的约束覆盖。

## 输入要求

- 必需输入：当前项目工作目录。
- 推荐输入：任务目标、涉及仓库、是否客户同步、是否 MCP、是否发布或外部交付。
- 缺失时处理：优先读取 `.maw/repository-identity.yaml`；缺失时按 `unknown_legacy` 兼容，不阻断普通开发，但涉及客户同步、MCP、发布、密钥或交付时必须先补身份判断。

## 执行步骤

1. 读取 `.maw/repository-identity.yaml`，确认 `current_repository.primary_role`、`current_repository.roles` 和 `role_status`。
2. 使用 `role_detection.detectors` 从目录结构和关键文件内容检测 `detected_roles`；不要只相信配置声明。
3. 对比 declared roles 与 detected roles。普通开发只 warning；客户同步、MCP 受控写入、发布、密钥处理、外部交付必须人工复核；MCP 角色错配 fail closed。直接 fork 的派生项目可能继承种子仓声明；当 Git `origin` 不等于 `.maw/template-source.yaml` 的 `template_source.git_url`，或用户明确说明当前仓库作为派生项目使用时，必须把复制来的 `seed_repository` 声明视为待修正身份，而不是源模板仓事实。
4. 按 `current_repository.roles` 顺序读取 `.maw/repository-identity.d/<role>/*.yaml`；同名约束以后读取的角色目录为最高优先级覆盖。
5. 对照 `role_catalog` 解释当前仓库职责、允许事项和禁止事项。
6. 读取合并后的 `role_boundaries`，确认可见面、可写面、受保护项目事实和客户可见面。
7. 读取合并后的 `constraint_interfaces`，按任务类型确认模板升级、项目升级、客户同步、MCP、宿主机用途、密钥治理、发布和 code 交付的 mode。
8. 如果任务涉及 MCP，读取 `docs/implementation/local-mcp-gateway/README.md` 和 `TINST-029`；MCP 返回的 repository roles 与本地有效身份地图不一致时 fail closed。
9. 如果任务涉及客户仓或外部交付，读取 `docs/customer-repository-sync-guide.md`、`.maw/customer-repository-rules.yaml` 和 code-only 导出规则。
10. 如果任务涉及模板升级或种子仓回流，先区分种子仓、主仓和派生项目仓，避免整包覆盖真实项目事实。
11. 需要给大屏或新会话输出时运行：

```bash
python3 ops/scripts/extract-project-metadata.py --section repository-identity --format markdown
```

## 验证方式

- `.maw/repository-identity.yaml` 可被 YAML 解析。
- `bash ops/scripts/check-repository-identity.sh` 通过。
- `python3 ops/scripts/extract-project-metadata.py --section repository-identity --format json` 可输出声明角色、检测角色、检测证据和已应用角色目录覆盖。
- `PROJECT_COMMANDS.md`、`docs/ai-instructions/README.md`、最终收口模板和配置读取说明已登记本指令。

## 禁区

- 不把宿主机用途当作仓库角色；`platform host` / `customer host` 是机器可见性，不是仓库身份。
- 不只依赖配置声明判断角色；必须结合目录结构和关键文件内容生成检测结论。
- 不只依赖 fork 后会被复制的 `.maw-template/template.yaml` 判断源模板仓；需要结合 Git 来源、当前项目事实和用户明确说明。
- 不把客户项目仓默认升级成主仓或平台项目仓。
- 不把种子仓当作主仓运行时代码承载仓。
- 不在客户项目仓暴露 Template Pack、内部 prompt、隐藏 workspace、完整内部 Git 历史、真实密钥或未脱敏日志。
- 不在未知历史仓里凭空假定客户/平台角色；证据不足时写 `unknown_legacy` 并提示待分类。

## 冲突与覆盖规则

- 用户最新明确说明优先，但必须同步更新 `.maw/repository-identity.yaml` 或说明为何暂不更新。
- 当前仓库真实 `README.md`、`code/`、app_key、发布配置、仓库映射、secrets 和模块档案优先于种子仓默认值。
- MCP 返回身份或角色集合与本地有效身份冲突时，以安全为先 fail closed；不要继续执行受控写入或客户同步。

## 更新记录

- 2026-06-17：创建，新增仓库身份地图、差异化约束接口、提取和校验口径。
