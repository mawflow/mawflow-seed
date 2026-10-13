---
doc_key: migration.seed-source-policy-20261014
doc_type: governance
stage: governance
status: active
owner: project-owner
tags: [seed, source-route, template-upgrade]
read_contract:
  summary: "统一主仓绑定内部 Seed、其它派生项目公共稳定版的现行口径。"
  ai_read_hint: "校正旧来源说明或采用本次规范修订时读取。"
---

# Seed 来源口径统一

只有经共享项目身份、仓库角色和 Git origin 核验的主仓使用注册绑定的内部 Seed 独立 Git 目录，冻结已提交固定 commit。其它所有派生项目，包括内部开发仓，使用经验证的公共稳定 tag 与同版本 Kit。本机 overlay、用户参数和历史来源字段不能改变路线。

本轮校正规范、配置说明、指令与经验入口，使其与现有 Seed Kit 来源实现一致。Seed 开发仓保留自身身份；不把其 内部来源通道 声明复制为业务项目的内部来源许可。Git Seed 的完整规范入口与 Kit 物化的升级策略、漂移指令使用同一边界，Kit 的公共来源默认值保持不变。

## 采用与保护

- 主仓仅从注册 code-source binding 解析目录，并核验独立 Git 根、origin、干净工作区及固定提交；绑定缺失或不匹配时停止，不使用任意本机路径、私有 URL 或当前仓库兜底。
- 其它派生项目核验公共稳定 tag、Payload Manifest、Seed lock 与同版本 Kit；不采用 main、rc、任意 commit、私有源或本机目录覆盖。当前开发源尚未公共发行时等待正式发行，不绕过公共路线。
- unknown_legacy、旧内部来源和不可达基线保留现有状态，先输出证据、预览来源迁移；不直接换 URL、清空或改写 applied_version。
- 增量合并当前规则入口，保护 README、code、真实 app_key、发布配置、仓库映射、模块档案、本机绑定和秘密。
- 不批量修改历史来源、旧迁移回执、手动 prompts 或其它项目；不推进主仓完整 adopted SHA、正式 tag、公共版本或 Host 安装状态。

## 验证与发布

来源行为复验使用 tests/test_template_source_policy.py 和 tests/test_plan_template_drift.py；规范检查使用模板模块、技术地图、AI框架及本机边界检查。Git 与 Kit 的漂移指令和本迁移说明应逐字一致。

本轮是开发分支规范修订；提交、推送及本地验证不等于公共 Seed/Kit 发行、Host 更新、其它项目采用或真人验收。
