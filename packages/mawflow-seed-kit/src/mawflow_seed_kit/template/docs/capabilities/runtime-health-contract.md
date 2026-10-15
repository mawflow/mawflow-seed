---
doc_key: capabilities.runtime-health-contract
doc_type: capability
status: active
owner: platform
---

# 可选项目运行健康协议 v1

运行健康用于回答“某个项目、环境和逻辑实例现在是否正常，有哪些可核实的异常”。它与项目诊断中的研发资料、Seed 完整性、项目健康上下文并列；运行异常不改写项目评分、任务状态或发布结论。

## 接入选择

| 项目情况 | 方式 | 项目需要做的事 |
| --- | --- | --- |
| 暂不需要运行巡检 | 不接入 | 无需新增文件、安装服务或配置凭据 |
| 已有完整诊断能力 | `native` | 在原有权限和租户边界内提供标准 GET 投影，继续使用原生诊断引擎、缓存、历史和页面 |
| 只有零散健康接口 | `sidecar` | 显式部署可选采集组件，声明有界 GET 检查，由组件保存脱敏快照 |

Seed 只分发示例、契约和离线校验。`.maw/runtime-health.example.json` 默认关闭；只有项目自行创建 `.maw/runtime-health.json` 才算声明接入。该文件缺失或 `enabled:false` 返回成功和 `not_adopted/disabled`，不扣分、不阻断 Doctor、不安装组件、不探测网络。声明也不授予部署或访问环境的权限。

示例：[原生接口](examples/runtime-health-native.json)、[独立采集](examples/runtime-health-sidecar.json)。声明格式由 [.maw/schemas/runtime-health.schema.json](../../.maw/schemas/runtime-health.schema.json) 描述；检查键必须唯一。

```sh
python3 ops/scripts/check-runtime-health.py --root . --format json
```

检查器只读声明，退出码 0 表示未采用、关闭或声明有效，20 表示声明无效；声明有效不代表服务健康。正常运行不会生成任何项目文件。

## 共享声明和环境绑定分开

共享声明只写检查键、类别、逻辑目标、GET 路径和断言，或原生路径、覆盖范围、响应封装。禁止在共享声明中写实际 URL、凭据、任意命令、SQL、修复动作。生产地址和凭据只由运行环境或本机受控配置提供。

原生接口可以直接返回标准对象，或显式声明 `common-result`，由 `{"code":0,"data":标准对象}` 封装。非 0 code 必须失败；工作台不猜测封装，不自动登录，不创建长期管理员 Token。

独立采集模式支持：

- `availability/readiness/dependency/version/backlog/heartbeat/business` 七类检查。`key` 区分同类的多个检查；`required` 表达已知失败是否阻断。
- `http_status` 只接受 HTTP 200；`json_equals` 比较 JSON Pointer 的标量及其类型；`json_number_max` 比较非负有限数值；`json_age_seconds` 检查带时区的 ISO 时间戳。
- 最多 16 项、最多 4 项并发。GET 不跟随重定向，不执行表达式或脚本。未知字段、写方法和不受支持的断言应拒绝。
- 检查目标必须是项目明确保证无业务写入的接口；GET 方法本身不能证明服务端没有副作用。

## 标准结果

正常快照使用 `schema=mawflow.runtime_health.v1`，字段见 [结果 schema](../../.maw/schemas/runtime-health-snapshot.schema.json)。必要字段：

| 字段 | 含义 |
| --- | --- |
| `project/environment/instance` | 服务端权威身份；消费者必须与本地预期逐项匹配；instance 可为明确标注的租户逻辑服务，不能冒充物理节点 |
| `scope` | 实际覆盖范围；例如课程研发，不能据此宣称整个业务系统健康 |
| `adapter` | `native-v1`、`declarative-http-v1`，或既有 `actmp-course-rd-v1` 兼容投影 |
| `snapshot_id` | 32 位十六进制读取/采样标识；原生读取标识不代表持久化诊断历史 |
| `checked_at/source_checked_at` | 摘要和底层证据时间，必须含时区；缓存不能刷新底层证据时间 |
| `stale_after_seconds` | 2—86400 秒有效期，按底层缓存与巡检间隔明确选择 |
| `configuration_current/freshness` | 结果是否属于当前配置；`fresh` 或 `stale` |
| `status/code/checks` | 总状态、稳定原因代码和脱敏检查项；不输出源日志、SQL、账号、异常正文或任意远端文本 |

状态为 `healthy/degraded/blocked/unknown`。已知必要项失败是 blocked，可选项失败是 degraded；缺证、鉴权/连接/解析失败是 unknown。汇总优先级 blocked > unknown > degraded > healthy。只有完整、当前、未过期且全部检查为 healthy 才能显示健康。不存在“缺失等于零”的回退。

消费者用自身时钟重新计算摘要和证据时效，超过 TTL 或未来超过 30 秒都不得继续显示绿色。配置改变后旧快照不能代表现状。停采集、工作台断网、切换项目或身份不匹配也应清除旧绿色结果。历史保留“当时状态”，必须明确标为历史。

尚未采集时可返回 `schema`、三项身份、`status:unknown`、`code:not_collected`、`freshness:missing`、`checks:[]`；这不算健康证据。

## 工作台与运维边界

本地工作台在项目诊断内显示运行健康，并允许切换显式绑定的环境、查看检查和已有快照历史、复制脱敏诊断任务摘要。访问必须经过本机解锁及已登记项目校验；浏览器不能提供任意探测 URL。

工作台本机绑定使用 `.local/config/runtime-health.json`，凭据为 `MAWFLOW_OPS_*` 环境变量引用；值不落共享仓库。原生模式直接 GET 已配置路径，并保留项目自己的历史；独立组件模式读取 `/v1/health` 和有界 `/v1/history`。没有绑定时只展示可选接入说明。

一期不支持重启、SQL 修复、任务重试、配置写入、告警外发或自动部署。独立组件只写自己的有界快照库，不写目标项目业务数据。本地测试、目标环境验证、正式发布、真人验收分别记录，不能互相替代。

## 兼容与升级

这是 additive 的可选协议，不改变 Seed Contract v2 必需项或已有项目来源锁。原生项目可先按协议提供接口；无需等待重新生成项目、安装独立采集组件或升级模板整包。已有 `.maw/runtime-health.json` 和本机绑定必须保留，升级仅合并文档/示例/校验器。Seed 公共发布与各项目实际采用是独立动作。
