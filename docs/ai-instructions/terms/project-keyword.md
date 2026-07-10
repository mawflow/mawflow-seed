# 术语：项目关键词

## 元信息

- ID：TERM-003
- 类型：术语
- 状态：启用
- 别名：关键词、任务关键词、特有名词、业务黑话、项目内叫法
- 适用范围：当前项目的用户消息、任务提示词、Story/Task、模块档案和执行记录

## 定义

项目关键词是当前项目里会影响 AI 理解任务边界的短语或名词。它可能是模块别名、页面俗称、接口简称、数据表简称、客户/环境/发布目标别名，也可能是人工在任务提示词里反复使用的业务概念。

用户澄清、说明和纠偏中出现的关键词也属于关键词学习范围。此时不仅要记录词，还要把可复用的说明内容暂存到 `docs/ai-instructions/experience-candidates.md`。AI 自己试错后找到正确方法时，也要把相关关键词和执行经验暂存到 `docs/ai-instructions/execution-lesson-candidates.md`。

项目关键词不等于普通技术词。只有当它会影响“读哪些文档、改哪些路径、归属哪个模块、调用哪个接口、涉及哪些表、发到哪个环境、哪些内容不能碰”时，才需要沉淀。

## 映射关系

- 候选台账：`docs/ai-instructions/keyword-candidates.md`
- 经验索引：`docs/ai-instructions/experience-index.md`
- 经验候选：`docs/ai-instructions/experience-candidates.md`
- 执行经验候选：`docs/ai-instructions/execution-lesson-candidates.md`
- 解决方案详情：`docs/ai-instructions/solutions/`
- 正式术语目录：`docs/ai-instructions/terms/`
- 相关指令：`docs/ai-instructions/instructions/keyword-learning-loop.md`
- 相关模块索引：`.maw/modules.yaml`
- 相关模块档案：`docs/modules/<module-key>/module.md`

## 使用场景

- 用户提示词中同一短语多次出现，但没有完整定义。
- 用户说“这个页面”“这个接口”“客户云”“设备端”“主流程”等项目内叫法。
- 关键词会决定 Codex 读取哪个模块档案、代码路径、接口文档或发布规则。
- 多次任务后需要把粗略理解升级为稳定术语。
- 用户在对话中补充“这个词以后表示什么”“这个边界怎么判断”“刚才理解错了”等信息。
- AI 在执行中发现“刚才命令错了、正确命令是…”“默认版本错了、应使用项目指定版本”等信息。

## 易混淆项

- `prompts/`：一次性任务输入，不负责长期沉淀关键词。
- `docs/ai-instructions/keyword-candidates.md`：关键词候选和边界草稿。
- `docs/ai-instructions/experience-index.md`：经验命中入口，先索引后读取详情。
- `docs/ai-instructions/solutions/**`：大型解决方案详情，不主动全量读取。
- `docs/ai-instructions/terms/*.md`：已经相对稳定的正式术语定义。
- `docs/modules/`：功能模块边界文档；关键词可以指向模块，但不替代模块档案。

## 注意事项

- 不记录真实密钥、token、账号密码、客户隐私、生产连接串。
- 不把归档旧词自动恢复成当前术语。
- 用户最新明确解释优先于旧记录。

## 更新记录

- 2026-05-20：创建项目关键词术语，作为关键词学习循环的基础概念。
