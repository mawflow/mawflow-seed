# 指令：UAT 业务交付

## 元信息

- ID：TINST-041
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/uat-business-handoff.md`
- 推荐调用：`#UAT交付 <模块或业务范围>`
- 精确调用：`#T041/<模块或业务范围>`
- 触发词：#UAT交付、UAT 交付、模块验收说明、业务验收文档、测试与审计版、逐模块交付测试
- 适用范围：为测试人员和审计者生成业务自述优先、带测试引导和证据状态的不可变 UAT 交付文档。

## 目标

从项目权威事实和本批次真实证据生成《业务验收说明（测试与审计版）》，写入测试与质量手册，使其可在本地工作台阅读并由有权用户选择后分享至云端工作台。

## 输入要求

- 必需输入：正式叶子模块、菜单或可解析的业务范围。
- 可选输入：重点角色、重点场景、目标环境、已知限制、目标交付状态。
- 缺失时处理：先通过 `.maw/modules.yaml` 和 `docs/modules/` 定位范围；业务事实不足时生成 `draft` 并明确“待业务确认”，不得猜测。

## 执行步骤

1. 读取 `docs/delivery/uat/business-handoff-standard.md`、模块档案、需求/设计、当前代码、组件测试入口和已有质量证据。
2. 将菜单或自然语言范围解析为正式叶子 `module_key`；存在歧义时先确认，不把一级模块组冒充可验收叶子模块。
3. 用第一人称角色叙事整理业务背景、价值、主流程、范围、变化、权限和终态；业务自述必须先于测试矩阵。
4. 运行本批次自测并保留项目根相对证据引用。测试失败或未运行时保持 `draft`。
5. 基于 `docs/delivery/uat/templates/uat-delivery-spec.example.yaml` 创建项目自有输入 spec；不得把模板示例当作真实业务事实。
6. 先运行生成器 `--dry-run --format json`，通过后使用新的 `delivery_id` 正式生成。禁止覆盖历史批次。
7. 验证文档、manifest、敏感信息和 Git 状态；业务文档写入 `docs/handbooks/quality/uat/<delivery_id>/`，内部证据留在项目自有非分享目录。
8. 本地工作台应能发现该 Markdown。只有用户明确要求分享且具备项目管理权限时，才选择测试人员需要的页面创建云端冻结分享；默认 7 天、允许评论、禁止下载。
9. 测试实际结果进入 TestRun/Bug/Evidence；分享锚点评论可转 Finding/修复任务。文档审阅 `approved` 不得写成 UAT 通过。
10. 收口报告 `delivery_id`、状态、模块、源提交、输出路径、自测、环境回读、分享状态、TestRun/Bug 引用、阻塞和责任人。

## 验证方式

```bash
python3 -m py_compile ops/scripts/generate-uat-business-handoff.py
python3 ops/scripts/generate-uat-business-handoff.py --spec <项目根相对 spec> --dry-run --format json
python3 -m unittest tests/test_generate_uat_business_handoff.py
git diff --check
```

## 禁区

- 不编造业务流程、权限、测试结果、环境回读或真人验收。
- 不整库复制开发数据，不默认执行部署、数据库同步或云端分享。
- 不把内部技术证据、凭据、绝对路径、原始日志或未脱敏客户数据写入测试人员文档。
- 不覆盖既有 `delivery_id`，不把静态文档作为 TestRun/Bug 第二账本。
- 不把本指令并入 TINST-025；TINST-025 是普通事实稿，本指令有不可变批次和证据状态门。

## 冲突与覆盖规则

- 用户最新明确范围优先，但不得绕过事实、脱敏、权限和真人验收门。
- 派生项目已有项目专用 `#UAT交付` 时保留其 `PINST-XXX` 编号，并增量采用本标准、输出路径和审计字段，不重排项目指令。

## 更新记录

- 2026-08-11：创建 TINST-041，沉淀业务自述型 UAT 交付、工作台分享和审计边界。
