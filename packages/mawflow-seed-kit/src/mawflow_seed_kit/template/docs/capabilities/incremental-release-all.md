---
doc_key: capabilities.incremental-release-all
doc_type: capability
stage: development
status: active
owner: project-owner
tags: [release, git, seed]
read_contract:
  summary: 发布全部入口、按组件上次成功提交筛选、部分成功记录与重试。
  ai_read_hint: 使用发布全部或维护逐组件发布基线时读取；规划和状态声明不替代真实发布验证。
---

# 发布全部与逐组件提交基线

`capability_key: incremental-release-all`，复用 `TINST-014 / #发布`，不建立另一套部署器。

```text
#发布全部
#发布：发布全部
#发布全部 到 staging
#发布全部 到 production
#发布上线 全部
```

未指定环境时采用聚合后的 `releases.defaults.default_environment`；缺少默认值须显式补充环境。“全部”指选定部署目标的显式 `component_refs` 全部候选，继续按变化筛选，不是强制重发、不跨环境、不扩大到未配置组件。同一环境存在多个部署目标时必须给出 `--deployment-target`，不会猜服务器或把多个目标合并为原子事务。单组件原指令与中文测试/上线/生产口径保持。

```bash
# 只生成计划，不构建、部署或写成功状态
python3 ops/scripts/plan-release-components.py '#发布全部 到 staging' --deployment-target staging-app --format json
python3 ops/scripts/plan-release-components.py staging --all --deployment-target staging-app --format json
# 实际发布并验证成功后，只记录成功组件；填入当次冻结的候选提交
python3 ops/scripts/plan-release-components.py staging --all --deployment-target staging-app --candidate-commit <本次实际发布的完整提交号> --record-success --successful-component api --record-path <发布验证记录> --format json
```

`--all` 与 `--component` 互斥；需要部分发布时只使用重复的 `--component <app_key>`。规划保留正式发布来源、生产clean/latest、SQL/迁移、审计和回滚要求。脚本生成计划，不自动执行项目私有部署命令；Agent按现有发布链执行，生产仍经过项目的正式发布门。

每个 `(environment, deployment_target_key, app_key)` 保存独立的最后成功发布状态：

```text
artifacts/release-state/<environment>/<deployment_target_key>/<app_key>.json
```

记录完整 `released_commit`、兼容的 `source_commit/version_id`、来源仓库、项目定义提交、部署范围指纹、发布时间、验证声明、发布记录引用；外部Git组件使用其独立仓库提交，不用外层仓库提交代替。旧 `<environment>/<app_key>.json` 与旧commit字段只读兼容；新记录写目标隔离路径，并原子替换单组件状态。

| 情况 | 结果 |
| --- | --- |
| 没有成功记录 | 纳入首次发布，不能称已经发布 |
| 同一提交、范围相同、上次及本次均为干净源码 | 跳过 |
| 提交前进，组件源码、覆盖层或共享发布路径变化 | 纳入 |
| 提交前进，仅其它组件或普通文档变化 | 跳过，保留原来的实际成功提交 |
| 部署目标/范围/策略指纹变化 | 纳入 |
| 本次组件有dirty变化或上次为dirty测试快照 | 纳入，不仅凭Git SHA跳过；生产仍拒绝dirty |
| 状态损坏、明确未验证、提交不可解析、倒退或分叉 | 阻断，先恢复或确认基线，不自动覆盖 |

多组件成功写入必须用重复的 `--successful-component` 列出实际已部署且验证成功者；未声明、失败、取消、范围外和已跳过组件不推进。单个待发布组件保留旧 `--record-success` 兼容，但仍只可在真实成功后调用。该参数是执行者的成功声明，脚本无法证明远端已部署；发布验证记录和目标读回仍是证据。

例如 api/web 均待发布，仅api成功：只推进api状态，web保留旧基线；下次发布全部跳过未再变化的api并继续列出web。整体失败不得把所有候选统一标成成功。无变化时输出空的实际发布名单，不执行部署。

## 会话收口

按 [发布全部的会话收口](../ai-coding/release-closeout.md) 展示逐组件提交和状态，优先统一入口，保留单组件选择。简短确认只绑定已明确列出的具体计划；显式发布全部按目标全部候选规划，显示此前遗留待发布项。无需业务发布或已有授权时不重复请求确认。

## 采用边界

Git Seed及Kit物化均携带规划脚本、配置读取器、说明和入口。已有派生项目通过自身模板升级增量采用；保留项目真实组件、部署目标、发布命令和已有状态，禁止导入源Seed真实发布状态。源码开发完成不代表公共Seed/Kit发行、主仓采用、Host更新、真实应用发布或真人验收。

迁移取舍与专项回执见 `docs/template-migrations/20261015-incremental-release-all.md`。
