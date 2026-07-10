# 指令：项目记忆闭环

## 元信息

- ID：TINST-022
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/project-memory-loop.md`
- 触发词：#项目记忆、#本机记忆、记忆闭环、越用越聪明、用户澄清、长期偏好、本机差异、local_update、memory_update
- 适用范围：任务开始前的记忆检索、任务结束后的项目经验沉淀、本机 `.local` 差异记录、多设备协作。

## 目标

让 AI 在每次任务中先查相关记忆，结束时把可复用信息沉淀到合适位置，让项目越做越清楚，同时避免把本机私有信息写进共享仓库。

## 存放边界

- 项目共享术语、用户澄清、长期偏好、执行经验、触发词、用户习惯用语、别称和正式指令：写入 `docs/ai-instructions/`。
- 任务包恢复状态：写入对应任务包的 `SESSION_STATE.md`。
- 任务执行记录、可提交产物记录：写入 `artifacts/ai-runs/` 或任务约定目录。
- 本机路径、端口、工具链、代理、浏览器调试、本机 SSH key 路径、本机维护记录、本机临时状态：写入 `.local/`，默认不提交真实内容。
- 派生自本种子仓库的项目，发布、回滚、健康检查或排障经验如果包含本机、服务器、凭证位置、端口、路径、审批窗口或环境差异，应优先写入 `.local/ai/` 或 `.local/maintenance/` 的被忽略文件，并在最终说明 `local_update` 中报告；脱敏后可复用的通用规则再抽象到 `docs/ai-instructions/`。
- `.local` 只提交 README 和 `.example.yaml` 示例。

## 执行步骤

1. 任务开始时，用用户消息、任务包、路径、命令和错误症状检索 `docs/ai-instructions/README.md`、`experience-index.md`、`keyword-candidates.md`、`experience-candidates.md`、`execution-lesson-candidates.md`。
2. 如果任务涉及本机差异，读取 `.local/README.md`、`.local/ai/README.md`、`.local/config/README.md` 和相关 example 文件。
3. 执行过程中遇到用户澄清、术语、简称、别称、习惯用语、偏好、执行经验或本机差异时，先判断存放边界。
4. 项目共享信息写入候选台账或正式文档；本机私有信息只写 `.local/`，不要提交真实值。
5. 用户习惯用语或别称含义已经明确后，后续任务的主展示和收口说明优先沿用用户口径；技术元数据的英文 key 保持稳定，值可以用用户口径解释。
6. 最终说明输出 `memory_update` 和 `local_update`，说明是否更新了项目记忆、本机记忆、候选台账、正式指令或经验；如本轮确认或沿用了用户口径，也简要说明。

## 本次模板默认偏好

- 可信设备开发：模板默认面向受控开发节点和私有仓库，但外部交付仍需脱敏。
- 业务项目默认只交付 `code/`，AI 控制面用于内部协作、验证和交付检查。
- `.local` 强化：多设备本机差异留在本机，真实资料和真实配置默认不提交。
- 多设备开发：可提交文档中的项目路径使用项目根相对路径，本机路径只进入 `.local` 或当次执行输入。
- 越用越聪明：用户澄清、长期偏好、执行经验、关键词、习惯用语和别称应持续沉淀。
- 用户口径优先：当用户习惯用语或别称已经确认含义，AI 后续收口主展示尽量使用用户叫法，例如“提主”“客入”“跑包”等；如含义仍不明确，先问清楚。

## 验证方式

- `docs/ai-instructions/README.md` 和 `PROJECT_COMMANDS.md` 已登记本指令。
- 候选台账表头存在。
- `.local/ai/README.md`、`.local/config/README.md`、`.local/device.example.yaml` 存在。
- 最终说明包含 `memory_update` 和 `local_update`。
- 已确认的用户习惯用语或别称，在最终说明主展示中按用户口径表达；技术元数据仍保留稳定 key。

## 禁区

- 不得把真实密钥、token、cookie、账号密码、客户隐私、生产连接串写入记忆。
- 不得把本机真实路径、代理、端口、SSH key 路径写进共享 docs；只写 `.local` 私有文件或 example 占位。
- 不得把一次性任务提示词当作长期指令；长期规则应沉淀到 `docs/ai-instructions/`。
