---
doc_key: migration.seed-upgrade-source-routing
doc_type: migration
stage: development
status: active
owner: platform-engineering
tags: [seed, template-upgrade]
read_contract:
  summary: "主仓独立 Seed Git 目录与其它项目公共稳定发行的统一升级路由。"
  ai_read_hint: "升级来源或旧私有基线迁移时读取；候选实现不代表公共发行。"
---

# Seed 2.12.0 升级来源路由

本次为开发候选；Seed Contract 保持 2。公共发行必须经过既有 Kit、公开 Git 和外部回读发布门，不能用开发提交替代公共稳定版本。

| 仓库角色 | 升级来源 | 解析与采用 |
| --- | --- | --- |
| 平台主仓 | 注册的独立 Seed Git 目录组件 | 核验共享平台身份及真实 origin，读取 code-source binding，校验独立 Git 根、来源 origin、忽略边界及干净状态，冻结 HEAD SHA；增量采用后记录 applied_version |
| 其它所有派生项目，含内部开发仓 | 官方公共稳定发行 | 默认 latest_verified_stable；公告只用于发现 tag，再回读 tag 的版本、Payload Manifest、Seed lock、同版本 Kit checksum 和 manifest |
| Seed 源仓 | 自身开发历史 | 生成升级资产、验证候选；不把自身开发身份当作派生项目目录升级权限 |

唯一实现是 Kit 的 `commands/template_policy.py` 与 `commands/template_drift.py`。仓库脚本及 `mawflow-seed-kit project drift` 调用同一实现；Host/CLI 发布包须匹配 Kit 后再验收，用户级安装不修改 Host 隔离依赖。

其它项目拒绝 main、dev、rc、任意 SHA、私有地址和本机路径覆盖。旧 主仓专用目录通道 配置返回 public_source_migration_required；未知角色返回 source_channel_unconfirmed；旧 applied_version 在公开历史不可达返回 source_baseline_migration_required。不得直接重写基线或倒退契约。先审计项目现有版本、Contract 指纹及公开 payload 对应关系，生成受控迁移预览、差异与备份，再采用并回读。公共发行低于项目已采用锁版本时返回 public_release_behind_project，保留项目状态。

来源缺失、不可信、工作树脏、发行物部分可用或摘要不一致时停止，不产生可执行升级提示词，不回退私有源、旁置目录或当前仓库。升级继续保护 README、code、真实 app_key、组件、模块档案、发布与仓库配置、secrets 及 .local。

候选采用与发布验收拆开：主仓及隔离 fixture 检查 Git/Contract 双漂移、错误来源、旧基线、部分发布、包损坏和配置覆盖；其它业务项目等待公共稳定发行后按各自事实迁移。本次没有批量修改其它开发仓，也没有执行公开发布、Host 下发或真人验收。

自动验证：92 项 Seed 定向测试通过，版本族对齐和 Seed 分发就绪检查通过；wheel/sdist 构建、twine check、用户级 pip check 通过。测试源码为 `tests/test_template_source_policy.py`、`tests/test_plan_template_drift.py`、`tests/test_seed_version_alignment.py`、`tests/test_seed_kit_v2.py` 和 `tests/test_portable_cli.py`。
