---
doc_key: migration.task-lifecycle
doc_type: governance
stage: development
status: active
owner: project-owner
---

# 任务生命周期与资源收尾增量采用

采用唯一权威 `docs/ai-coding/task-lifecycle.md`，共享Agent入口引用它，六阶段索引只引用不复制正文。旧任务快照没有lifecycle扩展时明确not_adopted，原有开发不阻断；新增任务按本规范，进行中任务在安全恢复点补齐，不回写历史。

Git Seed与Kit同版携带规则、Schema、例子、检查实现及升级资产。已采用项目有界审计后语义合并Agent入口、资源/收口规范、阶段目录和检查器；保留项目身份、源码、模块、发布配置、既有状态机、来源历史和设备绑定。不要从源仓复制真实任务记录、更新片段或私有资源清单。

文件侧`validate-task`验证声明与证据哈希，不能证明真实授权、进程退出、浏览器控制交还或真人验收；运行器通过当前能力提供实际回执。没有该能力时保留unknown/pending_automatic及下一步，不自动安装Host、常驻清理器或绕过浏览器工具。本次不增加平台数据库状态、不修改受管Git职责、不更新已安装Host。

验证包含正常完成、失败/取消/等待/暂停声明、真人验收隔离、同尝试证据绑定、归属保护、自动回收待定、证据失效、只读零写入和Git/Kit同构；正式发行与真实工具/真人验收分别记录。
