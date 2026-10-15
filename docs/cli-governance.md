---
doc_key: governance.cli
doc_type: governance
stage: development
status: active
owner: seed-maintainer
tags: [cli, compatibility, read-only]
read_contract:
  summary: Seed CLI 版本方向、有界上下文和历史描述符兼容。
  ai_read_hint: 修改项目查询和迁移前读取；不包含 Host 平台实现。
---

# Seed CLI 查询与兼容治理

Seed Kit 持有通用项目契约、上下文和组件算法。Host 状态、账号安装、存储、资源缓存及 npm 包由平台主仓持有，不能反向复制到 Seed。正式发布与项目采用独立；本轮只形成开发候选，不改变版本、公开载荷、模板锁或派生项目完整采用基线。

- 编译结果新增 `tool_compatibility`。项目 Seed 版本或 Contract 高于工具时返回 `tool_upgrade_required`，问题码 `seed_tool_upgrade_required`；`editable=false`、`migration_required=false`。先升级工具，禁止旧工具生成或执行迁移。无法识别的版本返回 `unknown` 并拒绝写入；旧锁和同版本指纹变化保留原有迁移流程。
- 上下文正文每份最多读取 256 KiB，输出继续受字符预算限制。大文档返回前缀、`truncated=true`、实际字节数及 `hash_scope=read_prefix`；该哈希不代表全文。预算耗尽后的引用只校验安全路径并标记未载入。配置映射仍执行严格大小限制，软链接、私有目录和手工提示词禁读边界保持。
- 组件描述符兼容 `component.path` 与 `component.local_path`。至少有一个字段与项目登记路径一致，已出现的字段必须全部一致；冲突、错误 Key、逃逸路径继续拒绝，不改写项目描述符。
- `mawflow --read-only ...` 仅允许已审查查询及不保存计划的验证/补全预览；执行和保存计划入口在分发前阻断。该策略不授予执行权限，也不声称为操作系统沙箱。平台 facade 的账号策略由其 owner 检查。
- 外部源码查询使用 `git --no-optional-locks`，避免只读 status 刷新 Git 索引；回归核对真实索引、目录、mtime 和权限。

验证：`tests/test_cli_governance.py`、`tests/test_agent_portability.py`、`tests/test_seed_kit_v2.py`。测试使用合成项目，检查查询前后目录、内容、mtime 和权限；路径拒绝、工具版本方向和冲突检查均需保留。其它派生项目仅在后续经验证的公共版本发布后按自身流程采用，不读取平台本机绑定。

P2 通用输出、版本/profile 与 Doctor 摘要候选见 [P2 契约](cli-governance-p2.md)，不把未发行的同号源码当作已发布制品。
