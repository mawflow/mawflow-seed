# 对话开发资源协调采用说明

本次添加通用开发资源规范、标准库检查/串行运行入口及 Agent 启动和阶段检查义务。CLI 复用已安装版本支持的 `capabilities`、`agent status`、`project context`；Seed 可兼容读取明确的设备策略文件；工作台配置 UI 与同源 CLI 由主仓提供，无 CLI 时仍以项目入口继续开发。

新项目由 Git Seed 与 Kit 同时物化。已有项目先审计自身入口、验证命令与环境范围，再增量采用 `.maw-template/upgrades/20261010-development-resource-coordination.yaml` 中的文件与规则。保留用户规则、业务 README、code、真实组件、发布仓库配置和本机覆盖；不复制源仓来源收录或设备采样。

不更新 Seed Contract major，不宣称候选已公开发行。只采用本能力的项目保留原完整 `template_source.applied_version`，另行记录部分采用依据；其它派生项目按各自验证过的公共稳定源升级。并发门只约束显式包装的重任务，服务按需启动、内部测试worker和JVM预算仍由项目规范执行。

验收入口：`tests/test_development_resources.py`、`tests/test_agent_portability.py` 及模板/本机边界检查。正式发布与各业务项目采用需独立回执。
