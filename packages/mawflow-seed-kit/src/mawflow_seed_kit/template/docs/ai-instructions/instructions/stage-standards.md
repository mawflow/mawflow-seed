# 指令：阶段规范与任务清单

- ID：TINST-044
- 触发词：#规范、#阶段规范、#T044、阶段规范、规范清单。
- 适用范围：查询或治理六阶段规范、项目适用规则、任务深度及证据声明。

先读取 docs/standards/README.md 与 .maw/standards.yaml，根据阶段、task_class和task_kind选择命中规则，再读取它们的唯一权威正文；不全量加载docs、经验、prompts或账号内容。沿用用户已确认范围和项目事实；只读查询不写目录、生成索引、修改任务状态或发布。需要修改时按明确授权增量执行。

使用 python3 ops/scripts/manage-project-standards.py context/check；render先预览再按指纹执行；validate-task只核验声明与摘要，不证明授权、实际测试、发布或真人验收。未采用项目返回not_adopted，继续既有流程。范围外缺口按责任提报，不扩大到公共源码。

修改规范时维护稳定key、唯一权威、触发/适用条件、责任、执行方式、版本、例外和复用条件；保留现有TINST/PINST编号。运行索引检查、任务声明和相关协议验证，分别记录Git/Kit、公共发行、项目采用及真人验收。
