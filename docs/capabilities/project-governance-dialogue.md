---
doc_key: capabilities.project-governance-dialogue
doc_type: capability
stage: development
status: candidate
owner: project-owner
---

# 项目权威问答与档案闭环

capability_key: `project-governance-dialogue`。当前为 2.15.0 开发候选；共享核心已通过自动验证，Host 与真实项目旅程另行验收。

入口与契约见 [项目治理协议](../ai-coding/project-governance.md)。外部 AI 使用项目内离线工具或安装包 CLI，Host 使用已安装 Kit API；实现共源，源文件从不被当作脚本执行。

权威问答按稳定 key/scope 与显式版本关系解析，不按最新时间选胜者。AI提案不替代人工确认；来源声明、身份核验、AI读取、执行和验证独立。档案修订与问答变更使用单个来源完成标记，文件准备中断不会激活新口径。追加历史保持可追溯，身份与权限由调用方既有边界验证。

自动验证覆盖真实文件追加、精确重试、过期预览、确认分支覆盖、AI伪确认拒绝、证据变化、来源损坏、联合修订中断恢复、不可变档案及CLI读取。分享审计使用项目空间原有入口，不新增分享或审计主账。
