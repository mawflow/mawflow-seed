---
doc_key: governance.development-resources
doc_type: governance
stage: development
status: active
owner: project-owner
tags: [resources, local-development, host, agent]
read_contract:
  summary: "对话开发时的设备资源预算、跨项目重任务协调和本机工作台通信。"
  ai_read_hint: "本地开发开工、启动服务、构建或测试前读取；无需全量扫描项目和机器。"
---

# 对话开发资源与本机通信

所有采用本协议的 Seed 项目与 Agent 使用同一约定。项目共享文件仍是项目规则权威；工作台/CLI 提供能力和新鲜状态，不扩大当前任务的写入、发布或服务控制授权。设备绑定、预算差异及运行日志只留在本机。

## 开工与持续通信

1. 读取项目入口和当前模块，在本地执行 `python3 ops/scripts/development-resources.py check`。只读检查不创建锁、日志或配置。该入口有界调用 `mawflow capabilities`、`mawflow agent status`；声明 `project.agent_context` 时回读项目共享规则的来源哈希。单次调用超时5秒；不自动安装、登录、启动、升级或上传聊天。
2. 可用时实际读取 `mawflow project context --root . --module <当前模块> --max-chars 12000 --format markdown`；项目没有模块时省略 `--module`。脚本的哈希回执不能代替阅读正文，截断不能当作已读全部规则。CLI 缺失、旧版不支持或工作台离线时直接按项目文件开发，明确通信降级；不得猜命令或连接未登记端口。
3. 有当前项目已授权 Local MCP 时，可用其正式上下文/状态入口替代 CLI；先核验工具发现、项目绑定、只读范围和返回契约，不绕过既有认证。没有已注册入口就用 CLI；CLI 的能力可用与工作台的健康就绪分别记录。
4. 在会话恢复、切换项目/模块、启动服务前、重任务前后及里程碑再次检查。正常写代码不后台轮询。受管长任务每60秒有界更新本机状态，完成后再回读；通信失败只降级，不安装任何常驻进程。不向工作台写聊天内容或创建影子任务；PM 状态仍按既有受权入口推进。

无执行能力的网页 Agent 提供待执行检查与未验证说明；工具、MCP、Skill 均不是读取项目规则的前置条件。

## 工作台配置一次，设备项目共用

本地产品工作台的“设置 → 开发资源”提供 Docker 本机/远程服务器选择，复用已有 SSH 或验证证书的 TLS Docker context，并可只读测试连接。配置属于当前 OS 用户与设备，保存在用户目录下 `.local/config/maw-development-resources.json`（`mawflow.development_resource_policy.v1`），不复制到每个项目，不随 Git 或云账号同步。配置只含执行位置、context 名称及串行预算，不保存凭据或连接串。

工作台与 `mawflow development-resources show/configure/probe` 使用同一配置和版本校验，保存/测试沿用 loopback、本机会话、CSRF 和 Origin 保护。未配置时本机默认；无效配置阻止受管执行。支持 `host.development_resources` 的 CLI 优先回读；旧 CLI 或缺失时，Seed 检查器仅有界读取这一明确声明的设备策略文件，仍可消费工作台选择，不扫描其它本机目录。

```bash
mawflow development-resources show
mawflow development-resources show --contexts
mawflow development-resources probe --context <已有远程连接名>
# 配置缺省只预览；--execute 保存同一方案，版本取 show 的 revision
mawflow development-resources configure --mode remote --context <已有远程连接名> --expected-revision <revision>
```

Agent 在每次资源检查后实际读取 `device_policy`：Docker 任务用下述 `--workload docker` 入口，包装器为子进程注入选定的 `DOCKER_CONTEXT` 并清除冲突的 Docker 目标环境变量，不改用户全局 context。远程任务先核对 context 是远程 SSH/TLS，再只读回读 Docker daemon；不可达或显式命令覆盖目标时阻止，不能静默回退本机。本机模式的 Docker 任务也核对实际目标；环境变量或全局 context 指向远程时停止并提示冲突，不把远程误认为本机。本地 npm/JVM 构建仍受本机内存准入；明确 Docker 远程负载单独验证远程 daemon，不因本机 warning/critical 一概拒绝，仍共享保守串行名额。远程服务器的内存总量不是空闲内存或其它设备任务预算，不能据此增加并发。

实际用到的 Compose 命令、服务命名、数据隔离、目录挂载、端口及源码上传/构建 context 继续由当前项目声明。Docker bind mount 属于 daemon 所在服务器，不能自动使用客户端本机目录；采用已有远程数据卷或项目受权的代码同步方案，依据 [Docker 挂载说明](https://docs.docker.com/engine/storage/bind-mounts/)。远程访问采用 [Docker 官方 SSH/TLS 连接方式](https://docs.docker.com/engine/security/protect-access/)，本功能选择已有连接，不安装远程 Docker、不修改防火墙、不上传源码、不迁移数据库。

项目有明确特殊目标或未满足远程挂载/隔离条件时，说明与设备默认的冲突并按项目授权处理；不得把设备默认当作上传数据、运行服务或发布授权。旧项目需采用本协议，文件 Agent 按入口执行检查；普通手工 Docker 命令和未采用规范的旧项目不会自动受控。

## 资源预算与最小环境

- CPU 空闲不证明内存充足；Swap 存量不证明当前持续换页；进程压缩内存统计不能直接相加为物理内存。历史单次采样是线索，决策使用本次状态。
- 默认只保留一个主要项目的必要环境，其它项目先做编辑、静态检查和有界单测。按当前模块依赖选择服务，复用已授权且版本、数据隔离满足要求的现有实例；禁止默认启动全部组件、重复 watcher、重复 JVM 或相同用途的容器。
- 构建、集成测试、镜像构建、大型索引和批量数据库导入等重任务，同一设备同一 OS 用户默认一次一个。测试命令内部的 worker/thread 也应按项目已支持的参数保守配置，不能用多个会话规避预算。小型只读搜索可并行；不要为了协调启动新的重型服务。
- JVM 堆上限、容器 VM 配额、服务并发由项目和设备实测确定，考虑非堆、数据库、IDE/浏览器、Host 与系统余量；不把某台机器的总内存或一次采样写成所有项目固定值。不在本任务中自动调参、删除数据、停服务或杀其它会话进程。
- 内存 warning 时保留串行名额并减少新增服务；critical 或无法可靠取样时暂缓新重任务、补充诊断。运行中的任务遇到压力只记录提醒，不自动杀任务。Apple XNU 的压力枚举0正常、1/2警告、3/4严重，与通知位掩码分开解释，依据 [Apple 内核说明](https://github.com/apple-oss-distributions/xnu/blob/main/doc/vm/memorystatus_notify.md)。Linux 按 `MemAvailable / MemTotal` 使用本协议保守阈值：低于20%警告、低于10%严重；这是准入建议，不是内核压力等级。

## 跨项目串行执行

```bash
# 先检查/预览，均不写入；-- 后是项目已授权的实际命令
python3 ops/scripts/development-resources.py check
python3 ops/scripts/development-resources.py run -- npm run build
# 执行同一命令并取得设备共享名额
python3 ops/scripts/development-resources.py run --execute --timeout-seconds 1800 -- npm run build
# Docker 重任务消费工作台设备设置
python3 ops/scripts/development-resources.py run --workload docker --execute -- docker build -t <项目镜像名> .
```

执行入口不使用 Shell 字符串；复杂管道应复用项目现有脚本。仅包装已授权且会退出的构建/测试命令，不用于长期服务启动或发布。跨项目锁位于用户级 MAWflow 本机状态区，由 OS 进程锁裁决，不扫描其它项目或私有会话。锁忙立即返回 `blocked`（退出码10），稍后复检；不进行无限等待。取得名额后再采样，阻止过期预览绕过压力检查。

正常完成释放名额；子进程继承同一锁，包装进程异常退出时仍在运行的继承子进程保留名额，避免以超时租约错误并发。超时与 Ctrl-C 只清理本入口启动的进程组。锁文件不删除以防不同 inode 同时持锁；命令输出保存到项目已忽略的 `.local/maw/development-resources/`，诊断不打印命令参数、环境变量、凭据或原始日志。返回日志相对路径、命令退出码与最新状态。

当前自动采样支持 macOS/Linux，进程锁支持 POSIX；Windows 和未知系统保留 `unknown/blocked`，人工串行并单独适配验收。锁只约束使用入口的同一用户，不是系统硬配额，无法限制手工 Shell、不同用户、后台服务或主动关闭继承描述符的程序。服务预算仍由 Agent 执行上述规范；不能宣称已实现全设备自动调度或已优化业务运行配置。

## 传播与验收

Git Seed 和 Kit 物化都包含规范、脚本、Agent 规则及升级资产；旧项目经自身模板升级增量合并，保护项目事实与本机配置。仅开发源提交不会让所有既有项目立即生效；公共稳定 Seed/Kit 发行、各项目采用、正式 Host 安装和真人验收分别记录。

验收覆盖只读零写入、CLI缺失/能力不支持/工作台离线、真实上下文回读、双项目互斥、包装进程崩溃后子任务持锁、超时清理、失败退出码和 Git/Kit 资产一致性。收口记录资源压力、通信状态、并发选择、服务复用/新增理由与未验证项。

任务开工、恢复与收尾按 `docs/ai-coding/task-lifecycle.md` 执行；分别说明执行结果、业务关闭与资源回收，等待/失败/取消/交接也清点资源。
