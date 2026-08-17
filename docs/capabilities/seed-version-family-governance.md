# Seed 统一版本族治理

MAWflow Seed 的公开 Git 版本、`mawflow-seed-kit` 版本和 Seed Contract 版本组成一个发布版本族。

## 版本规则

- `TEMPLATE_VERSION` 是唯一人工维护的完整 SemVer，公开 Git tag 与 Seed Kit 必须使用同一个 `X.Y.Z`。
- Seed Contract 不再维护独立的大版本号；`contract_version` 必须等于完整 SemVer 的主版本 `X`。
- 契约指纹继续由 Catalog 内容计算，用来识别同一大版本内的结构变化，不能用版本号替代。
- 大版本升级必须同时准备公开 Seed、Seed Kit、Catalog/Contract、BOM、lock 和公开 payload；任一项未同步，发布门失败关闭。
- 已发布的历史 `v0.2.x` 不改写。统一规则从 `v2.3.1` 候选线开始执行。

## 强制校验

```bash
python3 ops/scripts/check-seed-version-alignment.py --format json --strict
```

该检查会核对公开 payload、Python 包、Catalog、根 lock、初始化模板 lock 和模板元数据，并重新计算契约指纹。分发就绪、开源就绪和公开 payload smoke 都必须消费同一个检查结果。

## 产品工作台口径

本地产品工作台的“版本更新”同时展示公开 Seed、Seed Kit 和 Seed Contract，使用公开 Product Facts 的最新已验证稳定版本作为建议目标。公开源陈旧、三者主版本不一致或本机 Kit/Contract 落后时必须明确提醒，不能把候选版本当成已经发布。
