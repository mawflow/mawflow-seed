# 公共能力：对话开发资源协调

- capability_key: `development-resource-coordination`
- status: candidate
- owner_module: not_identified
- origin: seed_repository

Seed Agent 在开工和阶段检查时消费新鲜设备状态及 MAWflow CLI/工作台回读；同一用户的项目和 worktree 共用一个受管重任务名额。规则、边界与使用见 [开发资源规范](../ai-coding/development-resources.md)，执行入口为 `ops/scripts/development-resources.py`，只依赖 Python 标准库。

资源检查不自动启动/停止业务环境、不改设备资源配置、不上传会话；显式工作台保存才修改设备策略。现有 CLI 的能力握手、Agent健康和上下文回读可直接复用，设备策略由主仓 Host 工作台与 CLI 同源配置，Seed 消费兼容契约。可选已授权 Local MCP 继续采用现有项目认证。支持本机/远程 Docker 执行位置；资源准入与项目开发授权独立，文件读取可在 CLI 离线时继续。

验证：`python3 -m pytest -q tests/test_development_resources.py tests/test_agent_portability.py`。macOS/Linux 提供资源采样，POSIX 提供跨项目锁；Windows 与其它系统在自动执行上失败关闭。开发候选不等于公共发行、所有业务项目采用或真人验收。
