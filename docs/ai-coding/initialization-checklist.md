# AI 编码初始化待办清单

本清单用于项目初始化。完成前，AI 只应做资料归档、只读分析、规则补齐和低风险整理，不应直接开展大规模功能开发。

## 必须完成

| 状态 | 编号 | 待办事项 | 输出位置 |
|---|---|---|---|
| TODO | AIC-01 | 收集用户明确给出的代码边界、风格偏好、禁改范围和交付要求 | `user-provided-rules.md` |
| TODO | AIC-02 | 阅读根目录 README、`TEMPLATE_OVERVIEW.md`、`docs/`、`code/README.md` 和各端 `.maw.component.yaml` | 本清单备注 |
| TODO | AIC-03 | 分析各端技术栈、框架、构建工具、测试方式和目录结构 | `component-guides/*.md` |
| TODO | AIC-04 | 总结现有代码风格、命名习惯、错误处理、日志、接口和状态管理方式 | `ai-analysis-rules.md` |
| TODO | AIC-05 | 明确 AI 可改、慎改、禁改的路径和文件类型 | `user-provided-rules.md` / `ai-analysis-rules.md` |
| TODO | AIC-06 | 明确新增依赖、数据库变更、配置变更、发布随带文件的审批规则 | `coding-style.md` / `release/rules.yaml` |
| TODO | AIC-07 | 明确每个端的安装、启动、测试、构建命令，并校准 `.maw.component.yaml` | `component-guides/*.md` |
| TODO | AIC-08 | 明确测试最低要求：单元测试、集成测试、冒烟测试或人工验证方式 | `coding-style.md` |
| TODO | AIC-09 | 明确新增或调整内容后的文档同步判断规则 | `coding-style.md` |
| TODO | AIC-10 | 建立待确认问题清单，无法确认的规则不得隐式假设 | `docs/requirements/pending-questions.md` |
| TODO | AIC-11 | 按 app_key 补齐 AI 调试索引，默认明确 server/client；如项目新增独立前端或后台 app_key，再补齐对应 URL、数据库引用、API 引用和测试账号引用 | `.maw/app-runtime.yaml` / `.maw/secrets.yaml` |
| TODO | AIC-12 | 确认 test 的实际运行方式：默认优先本机 Docker 开发/测试，但已有远端测试机、共用数据库联调环境或用户特别说明时按事实补齐服务器工作目录、健康检查地址和部署凭证；缺少 Docker、Host Manager 或 Node Runner 等宿主机能力时记录 warning | `.maw/environments.dev.yaml` / `.maw/environments.yaml` / `.maw/secrets.yaml` |
| TODO | AIC-13 | 确认 git 使用策略：默认可使用本机 git 环境；如显式配置 deploy key 或 token，确认 key 存放在 `.ssh/` 或公共目录且不提交 git | `.maw/repositories.yaml` / `docs/git-credentials-guide.md` |
| TODO | AIC-14 | 如果启用 `repository_mode: external_mapped`，按 app_key 补齐组件客户仓库映射，并确认组件目录不保存客户仓库 `.git`，同步流程为人工显式先拉客户仓库、解决冲突并提交本仓库、再通过临时客户仓库工作副本推客户仓库 | `.maw/repositories.yaml` / `docs/customer-repository-sync-guide.md` |
| TODO | AIC-14R | 如果启用仓库级 mirror，补齐 mirror remote 或 URL，并确认 `ops/scripts/sync-repository-mirror.sh plan` 能给出正确 `Configured`、`Config source` 和自动同步状态 | `.maw/repositories.yaml` / `docs/repository-mirror-sync-guide.md` |
| TODO | AIC-14M | 如果启用 `component_mirrors`，按 app_key 补齐组件镜像仓库映射，并确认镜像仓库只允许当前项目仓库单向同步到目标仓库，禁止从镜像仓库反向拉取或覆盖当前项目 | `.maw/repositories.yaml` / `docs/component-mirror-repository-guide.md` |
| TODO | AIC-15 | 确认 AI 改完即 commit/push 的仓库权限可用，且 commit message 和提交说明使用中文 | `.maw/policies.yaml` / `docs/ai-coding/coding-style.md` |
| TODO | AIC-16 | `.maw/modules.yaml` 已按实际项目模块调整，核心模块能通过 `module_key`、页面路径、接口路径或数据表名定位 | `.maw/modules.yaml` |
| TODO | AIC-16D | 证据不足的新项目模块线索已进入渐进式发现区，未把 seed/candidate 直接写成正式 leaf | `.maw/module-candidates.yaml` / `docs/modules/_discovery/` |
| TODO | AIC-17 | 核心模块已有模块档案，至少包含功能描述、实现程度、页面/API/数据表边界和文档维护规则 | `docs/modules/<module-key>/module.md` |
| TODO | AIC-18 | `docs/archive/README.md` 已存在，并声明 AI/Codex 默认不读归档内容 | `docs/archive/README.md` |
| TODO | AIC-19 | AI 开发任务最终说明能输出模块档案更新判断 | `docs/ai-coding/module-dossier-rules.md` |
| TODO | AIC-20 | 关键词学习机制已启用，能记录任务提示词中的项目关键词、出现次数、粗略定义和边界补充 | `docs/ai-instructions/keyword-candidates.md` |
| TODO | AIC-21 | 经验候选机制已启用，能暂存用户澄清、说明、纠偏的标题、关键词和内容摘要 | `docs/ai-instructions/experience-candidates.md` |
| TODO | AIC-22 | 执行经验候选机制已启用，能暂存 AI 错误尝试后的正确方法、触发场景和验证方式 | `docs/ai-instructions/execution-lesson-candidates.md` |
| TODO | AIC-23 | 经验索引与方案详情库已启用，AI 可先检索 `experience-index.md`，大型 `solutions/**` 详情只在命中后读取 | `docs/ai-instructions/experience-index.md` / `docs/ai-instructions/solutions/README.md` |
| TODO | AIC-24 | 由项目负责人或维护者确认本清单完成状态 | 本文件 |
| TODO | AIC-25 | 输入资料整理、提示词、报告、交付说明和最终输出中，涉及当前项目目录或文件路径时统一使用项目根相对路径 | `.maw/policies.yaml` / `TEMPLATE_OVERVIEW.md` |

## 待确认问题

| 编号 | 问题 | 影响 | 负责人 | 状态 |
|---|---|---|---|---|
|  |  |  |  |  |

## 完成记录

| 日期 | 完成人 | 完成范围 | 备注 |
|---|---|---|---|
|  |  |  |  |
