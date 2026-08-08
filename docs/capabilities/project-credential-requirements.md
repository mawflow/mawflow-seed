---
doc_key: docs.capabilities.project-credential-requirements
doc_type: capability
stage: governance
status: active
owner: planner
tags:
  - credentials
  - secret-governance
  - project-readiness
project_health:
  dimensions:
    - ai_collaboration
    - project_audit
  evidence_level: canonical
read_contract:
  summary: "Seed 2.2 项目凭证 Requirement v2、本机 Binding v3、Doctor 与运行时注入契约。"
  consumes:
    - .maw/project.yaml
    - .local/.maw/project.yaml
    - .maw/secret-bindings.yaml
  produces:
    - credential_requirement_validation
  ai_read_hint: "新增项目凭证依赖、项目 readiness 或本机 credential binding 时读取。"
---

# 项目凭证需求与本机引用绑定

## 能力目标

让项目以机器可读方式声明运行和开发所需的 credential，而不把 secret value 写入项目事实文件。主仓或派生项目运行时可以消费该声明计算 readiness；Seed 只提供声明、示例、Schema 和检查器。

## 数据边界

| 对象 | 可提交 | 不可提交 |
| --- | --- | --- |
| `credentials.requirements` | 类型、字段、use mode、环境、主体范围、存储位置、资源/租约/runtime injection 约束 | credential value、真实账号、Host 私钥、具体生产绑定 |
| `.local/.maw/project.yaml` binding | requirement key、credential ref、环境、资源 ref、版本选择、脱敏 Host 标识、Git Access Profile | token、password、private key、connection string、解密字段 |
| Git Commit Identity | name、email、signing mode、signing key ref | Git remote token、SSH private key 明文 |

`.local/.maw/project.yaml` 使用 `mawflow.local_project_runtime.v3` 且必须被 Git ignore；模板只提交 `.local/.maw/project.example.yaml`。binding 只允许 `mawsec://`、`mawlocal://`、`mawproxy://`，资源使用 `mawresource://`，Git Access Profile 使用 `mawgit://`，提交身份使用 `mawgitid://`。

Requirement v2 的 `runtime.inject` 只允许子进程环境、owner-only 临时文件、DSN、Git helper、Docker/Kubernetes 受控通道、stdin/fd；禁止 argv、父进程永久环境、日志、任务产物和 AI prompt。

## Readiness 消费建议

Seed 不定义运行时数据库和 API。消费方计算 Project Credential Readiness 时，至少同时核对：

1. requirement 是否存在有效 binding。
2. credential type 和 required field/use mode 是否匹配。
3. 是否存在 active version。
4. Subject Grant 是否允许当前主体和动作。
5. `host_authorization_required=true` 时目标 Host 是否另行授权。
6. 密文对象、recipient envelope 和 lease 是否可用且未过期/撤销。

任一必需门缺失时 fail closed，并返回可修复的脱敏原因；不能把 Subject Grant 等同于 Host Authorization。

## 兼容策略

- 旧项目缺少 `credentials` 时按空需求兼容；已有 Requirement 增量补齐资源、租约和 runtime injection，不读取或复制 Secret。
- 旧 `.maw/secrets*.yaml` 明文仅允许 migration-only：升级本身可以完成，但 Doctor 未清零前禁止发布、镜像和外部同步。
- 目标项目已有自定义 requirement/binding 时按 key 语义合并，不整文件覆盖。
- Seed 默认 `server` / `client` 不影响目标项目真实 app_key。

## 验证

```bash
python3 -m py_compile ops/scripts/check-project-credential-contract.py
python3 ops/scripts/check-project-credential-contract.py --format json
python3 ops/scripts/check-project-credential-contract.py --local .local/.maw/project.example.yaml --require-local --format json
python3 ops/scripts/maw-seed-doctor-credentials.py . --fail-on-plaintext
python3 -m pytest -q tests/test_project_credential_contract.py tests/test_seed_credential_doctor_v3.py
```
