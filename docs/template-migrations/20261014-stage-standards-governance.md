---
doc_key: migration.stage-standards-governance
doc_type: governance
stage: governance
status: active
owner: project-owner
tags: [standards, lifecycle, upgrade]
read_contract:
  summary: "Seed 2.13.0六阶段规范、任务深度及证据独立治理的增量采用。"
  ai_read_hint: "采用本次版本时读取；保留项目事实、历史和授权。"
---

# 六阶段规范治理升级

新增 `.maw/standards.yaml` 分类引用目录、六阶段导航、总则/项目采用/任务清单/经验资源规范、三个pending结构示例、Schema及Seed Kit唯一检查实现。规则正文维护唯一权威；现有TINST/PINST和业务模块不重编号。新入口TINST-044；文档分类增加delivery，执行阶段独立分类。已有项目未采用时返回not_adopted，不阻断原开发。

只选择本次阶段、任务类型和small_change/iteration/formal_delivery深度，命中后读取必要正文。已有授权在原范围延续；公共缺口按责任处理。空套件、声明不一致、缺失/变化/跨环境/跨版本/跨范围证据不得称passed；实现、验证、外部集成、交付、部署与真人验收独立。工具只核验声明和哈希，不证明真实授权/活动或推进原PM/TestRun/Audit/Release。

主仓使用注册绑定内部Seed固定提交，其它派生项目只用已验证公共稳定tag与同版本Kit，不能由本机路径、参数、main或rc改路线。项目的技术栈、真实角色、租户、网络、客户分支与数据库规则继续由项目维护，不复制参考项目私有事实。

## 增量采用

- 增加缺失文件，现有规则按语义合并；保留README、code、app_key、项目方法论、发布、仓库、秘密、模块档案、本机绑定及历史。
- Git与Kit共享目录、规范、任务示例、Schema、适配器和迁移资产。Kit只携带模板，不携带源仓真实来源/更新/验收事件。
- 元数据与Agent路由增量合并；不要整文件覆盖项目capabilities/agent-entry等自有字段。
- 安装/使用同版Kit后调用 `python3 ops/scripts/manage-project-standards.py render`，按预览指纹执行，再check；三个示例保持pending。
- 旧授权、测试和环境回执保留原范围，变更仅使受影响证据失效。正式发行、项目采用、Host支持与真人验收分别记录。

## 验证

`tests/test_stage_standards.py` 覆盖只读、缺失采用、重复/危险引用、symlink、指纹并发、空suite、声明状态、证据哈希与来源/环境/范围失效、独立真人轴、模块禁改路径及真实Kit物化。目录check、版本族、公共payload、模板模块、AI框架与本机边界均需通过。
