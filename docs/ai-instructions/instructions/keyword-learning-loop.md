# 指令：任务关键词学习循环

## 元信息

- ID：TINST-004
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/keyword-candidates.md`、`docs/ai-instructions/experience-index.md`、`docs/ai-instructions/experience-candidates.md`、`docs/ai-instructions/execution-lesson-candidates.md`、`docs/ai-instructions/terms/`、`docs/ai-instructions/lessons/`、`docs/ai-instructions/solutions/`
- 触发词：关键词学习、关键词沉淀、任务提示词关键词、项目关键词、特有名词、业务黑话、用户澄清、用户说明、AI 试错、执行复盘、错误尝试、正确方法、经验暂存、越做越聪明、边界细化、名词定义

## 目标

Codex/Agent 在执行任务时，应从任务提示词和用户消息中识别项目特有关键词，并把它们的含义、边界和命中场景持续沉淀到项目指令库。同时，用户在对话中的澄清、说明、纠偏和有复用价值的补充信息，也应提取标题、关键词和内容摘要暂存为经验候选。AI 自己在执行过程中先错误尝试、再找到正确方法的情况，也应记录为执行经验候选。关键词多次出现时，应逐步补全正式术语定义；经验多次适用时，应升级为正式 lesson、instruction 或编码规则。

## 适用范围

- 用户任务提示词中出现模块名、页面俗称、接口简称、数据表简称、客户/环境/发布目标别名、用户习惯用语或别称。
- 同一个关键词在一次提示词中多次出现，或在多个任务中反复出现。
- 执行中发现某个词会影响代码路径、模块边界、发布目标、权限、数据表或验收方式。
- 用户明确要求“记一下这个词”“以后这个词指的是”“这个叫法代表”“这个习惯用语以后按这个口径说”等。
- 用户澄清某个判断、纠正某个默认路径、补充某个边界、说明某个偏好，且这条信息会影响后续任务执行。
- AI 执行命令、测试、构建、脚本、浏览器调试或发布检查时，先用错方法后定位到正确方法，且该经验可能复用。

## 不适用范围

- 普通技术词，例如 API、数据库、前端、后端、登录，除非在本项目有特殊含义。
- 一次性临时描述，且不会影响后续任务理解。
- 无复用价值的偶发失败，例如一次性网络超时、手误命令或外部服务短暂异常。
- 真实密钥、token、密码、客户隐私、生产连接串和不可外传资料。
- 归档资料中的旧词，除非当前任务明确要求历史追溯并确认仍有价值。

## 执行步骤

1. 开始任务时，快速扫当前用户消息和任务提示词，提取可能影响边界的关键词、澄清和说明。
2. 先查 `docs/ai-instructions/README.md`、`docs/ai-instructions/experience-index.md`、`docs/ai-instructions/keyword-candidates.md`、`docs/ai-instructions/experience-candidates.md`、`docs/ai-instructions/execution-lesson-candidates.md` 和相关 `terms/` / `lessons/` 索引，确认是否已有项目共享记忆。
3. 如果任务涉及本机路径、端口、工具链、代理、浏览器调试、本机 SSH key 路径或本机维护记录，再读取 `.local/README.md`、`.local/ai/README.md`、`.local/config/README.md` 和相关 example 说明，确认本机记忆边界。
4. 已有正式术语时，读取术语文档，并按术语边界执行。
5. 已有候选词时，更新出现次数、最近出现、粗略定义、边界补充、相关 `module_key`、相关路径或对象。
6. 新关键词、习惯用语或别称达到任一条件时，写入候选台账：一次任务中多次出现、用户强调其含义、会影响改动边界、会影响发布/环境/客户仓库/数据表判断，或会影响后续收口用词。
7. 用户澄清或说明有复用价值时，写入 `experience-candidates.md`，至少提取标题、关键词、内容摘要、适用范围和相关路径。
8. AI 试错后找到正确方法且有复用价值时，写入 `execution-lesson-candidates.md`，至少记录错误尝试/症状、正确方法、触发场景、验证方式和相关路径/命令。
9. 候选词多次出现且边界趋于稳定时，创建或更新 `docs/ai-instructions/terms/<keyword>.md`，并在 `docs/ai-instructions/README.md` 的术语列表登记；如果是用户习惯用语或别称，术语文档必须写清“用户怎么说”“AI 收口怎么说”和“不应误用的相近说法”。
10. 经验候选多次适用或用户要求长期保留时，创建或更新 `docs/ai-instructions/lessons/<topic>.md`、`docs/ai-instructions/solutions/<category>/<topic>.md` 或 `instructions/<topic>.md`，并更新总纲索引和 `experience-index.md`。
11. 执行经验候选多次适用或风险较高时，升级为 lesson、solution、instruction，或同步到 `docs/ai-coding/`、组件 guide、脚本 README。
12. 如果关键词或经验关联模块，也同步检查 `.maw/modules.yaml`、`.maw/module-candidates.yaml` 和对应模块档案是否需要补充别名、路径或边界说明。
13. 最终说明中简要写出本次是否更新关键词台账、用户经验候选、执行经验候选、正式术语/经验文档、本机记忆或 `.local` 示例，并填充 `memory_update` 与 `local_update`；如果本次确认了用户口径，后续收口主展示应沿用该口径。

大型经验详情读取规则：`docs/ai-instructions/solutions/**` 默认不主动读取；只有 `experience-index.md`、候选台账、用户明确路径或当前错误精确命中某条经验时，才读取对应单个方案详情文件。

## 正式术语最小内容

正式术语文档至少写清楚：

- 关键词、别名、适用范围和状态。
- 在当前项目里的定义。
- 关联模块、页面、接口、数据表、配置或发布目标。
- 触发词和用户常见说法。
- 收口口径：用户确认含义后，AI 主展示应优先使用的叫法。
- 不属于该术语的相近概念。
- 安全、脱敏、权限、环境或有效期边界。
- 更新记录。

## 经验候选最小内容

经验候选至少写清楚：

- 标题：用一句话概括用户澄清或说明。
- 关键词：后续任务可能命中的词。
- 内容摘要：用户原意、纠正内容、边界信息。
- 适用范围：仓库、模块、路径、环境或任务类型。
- 状态：candidate、refining、lesson_created、instruction_created、term_created、merged、ignored。

## 执行经验候选最小内容

执行经验候选至少写清楚：

- 标题：用一句话概括错误尝试和正确方法。
- 关键词：后续任务可能命中的词，例如 python 版本、测试命令、浏览器安全策略。
- 错误尝试/症状：发生了什么失败、误判或错误输出。
- 正确方法：最终有效的命令、路径、版本、配置来源或判断顺序。
- 触发场景：什么任务阶段容易再次遇到。
- 验证方式：如何确认正确方法有效。

## 冲突与覆盖规则

- 用户最新明确解释优先于旧候选和旧术语。
- 用户最新澄清优先于旧经验候选和旧 lesson。
- AI 新近验证成功的执行经验优先于旧候选，但如果与正式文档冲突，必须先修正文档或记录待确认。
- 候选台账与正式术语冲突时，以正式术语为准，并更新候选状态为 `merged` 或 `term_created`。
- 经验候选与正式 lesson/instruction 冲突时，以正式文档为准，并更新候选状态。
- 执行经验候选与正式 lesson/instruction/编码规则冲突时，以正式文档为准，并更新候选状态。
- `experience-index.md` 与 `solutions/**` 冲突时，以当前代码、`.maw` 配置和用户最新说明为准，同时修正索引或详情。
- 术语与当前代码、`.maw` 配置或模块档案冲突时，以当前代码和 active 文档为准，记录待确认并修正文档。
- `docs/archive/**` 默认不参与关键词学习，除非用户明确要求历史追溯。
