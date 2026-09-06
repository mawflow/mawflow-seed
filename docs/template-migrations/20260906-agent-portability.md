# Seed 2.8 跨 Agent 入口升级

先在种子仓完成协议、Kit、测试与分发验证；派生项目通过 `#模板升级` 比较 applied commit 和 Seed Contract，再执行受控迁移与项目事实增量合并。

采用：通用入口 schema 3、共享规则、短上下文、Codex/Claude/Gemini 入口、未知 Agent 回退、独立 Agent Doctor、有界上下文导出。
改写：项目身份、任务路由、团队提交与发布策略，保留目标事实。
跳过：源仓维护者规则、私有来源与项目业务代码。
保护：README、code、真实 app_key、模块档案、发布配置、仓库映射、secrets、.local、人工工具规则。

Seed 版本推进到 2.8.0，Contract 主版本保持 2。迁移有文件差异预览、哈希冲突保护和可验证回滚。专用入口使用受管区块；异常区块需要语义复核。

验证：`mawflow-seed-kit doctor agents .`、`python3 ops/scripts/check-agent-portability.py --check-distribution`、`python3 -m pytest -q tests/test_agent_portability.py tests/test_seed_kit_v2.py`。
公开 payload 和官网 wheel 必须分别验证，不以源目录成功代替实际分发成功。
