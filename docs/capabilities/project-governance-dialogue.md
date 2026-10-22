---
doc_key: capabilities.project-governance-dialogue
doc_type: capability
stage: development
status: candidate
owner: project-owner
---

# 项目权威问答与档案闭环

capability_key: `project-governance-dialogue`。当前为 2.17.0 开发候选；共享核心已通过自动验证，Host 与真实项目旅程另行验收。

入口与契约见 [项目治理协议](../ai-coding/project-governance.md)。外部 AI 使用项目内离线工具或安装包 CLI，Host 使用已安装 Kit API；实现共源，源文件从不被当作脚本执行。

权威问答按稳定 key/scope 与显式版本关系解析，不按最新时间选胜者。AI提案不替代人工确认；来源声明、身份核验、AI读取、执行和验证独立。档案修订与问答变更使用单个来源完成标记，文件准备中断不会激活新口径。追加历史保持可追溯，身份与权限由调用方既有边界验证。

自动验证覆盖真实文件追加、精确重试、过期预览、确认分支覆盖、AI伪确认拒绝、证据变化、来源损坏、联合修订中断恢复、不可变档案及CLI读取。分享审计使用项目空间原有入口，不新增分享或审计主账。

四项治理扩展及人工直接维护见[共享合同](../ai-coding/governance-suite.md)。协议v4与旧来源兼容读取，新旧写器不允许降级丢字段；内置基线任务使用已有task/run，初始化候选、只读审计和漂移修复分开。Seed不承担主仓模型调度、原件存储或工作台界面，实际采用与真人验收单独记录。

自然语言学习扩展`natural_language_learning.v1`复用同一来源和确认版本：候选理解、人工纠偏、带条件的词面召回、精确消费与同轮反馈形成可追溯链。新进程无需旧会话即可读取已确认案例；实际语义理解由Agent完成，不由相似度授予权限。接口、只读与过期保护见[治理协议](../ai-coding/project-governance.md)。
