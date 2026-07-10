# 指令：MCP Knowledge Runtime

## 元信息

- ID：TINST-040
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/mcp-knowledge-runtime.md`
- 推荐调用：`#MCP知识库`
- 精确调用：`#T040` 或 `#T040/MCP知识库`
- 触发词：#MCP知识库、#MCP安装、#MCP更新、#MCP同步、#MCP审计、#技术选型、#框架包、#风格包、#项目蓝图、#提示词包、#框架审计、#风格审计、#依赖审计、#资源包回流、MCP Knowledge Runtime、Framework Pack、Style Pack、Blueprint Pack、Prompt Pack、Check Pack、Verification Pack、Case Pack、Connector Pack、Pack Registry、Project Override
- 适用范围：查询、规划或审计 MCP Knowledge Runtime v1.1；维护 Pack registry、project override、locks、resolution preview、export/import 相关任务；判断种子仓、主仓、Framework Hub 和派生项目边界。

## 目标

让 AI 在遇到 MCP 知识库、Pack、registry、project override、四层优先级、strict lock、资源包导入导出或技术选型时，先按模板协议建立边界，再生成安全的 plan / preview / task pack，不把种子仓协议误当主仓运行时实现。

## 执行步骤

1. 先读取：
   - `docs/implementation/mcp-knowledge-runtime/README.md`
   - `docs/capabilities/mcp-knowledge-runtime.md`
   - `.maw/mcp.yaml`
   - `.maw/project-signals.yaml` 中 `SIG-20260702-mcp-knowledge-runtime`
2. 判断用户意图：
   - 查询状态或协议：返回 registry 层级、Pack 类型、锁定规则和安全边界。
   - 技术选型、框架包、风格包、项目蓝图：生成 resolution preview 或取舍矩阵，不直接安装。
   - MCP 安装、更新、同步、审计、导出、导入：先生成 plan / conflict preview / 任务包；真实写入、下载、导入、导出或发布前需要人工确认。
   - 资源包回流：判断属于当前项目私有 registry、MAW 主仓控制面、种子仓协议，还是独立 Framework Hub 任务。
3. 使用四层优先级：

```text
Project Local Override
  > User Personal Registry
  > Shared Global Registry
  > Official Registry
```

4. 若需要校验 registry 或示例 Pack，优先运行：

```bash
python3 ops/scripts/validate-mcp-registry.py --registry .maw/mcp/registry.example.json --locks .maw/mcp/locks.example.json --format json
python3 ops/scripts/check-mcp-packs.py --format json
```

5. 若目标是派生项目采用模板能力，走 `#模板升级` / `TINST-026` 的漂移升级，不整包覆盖目标项目。
6. 若目标是主仓控制面或 API，实现应在 MAW 主仓执行；种子仓只提供协议和离线骨架。
7. 若目标是官方 Pack 资源库，拆成 `mawflow-framework-hub` 或目标公开资源仓任务，不把远端仓创建当作当前项目普通文件修改。

## 收口要求

最终说明必须写明：

- 当前输出是 preview / plan / protocol，还是已写入项目 registry。
- 是否触发真实安装、下载、导入、导出、发布或 Host Program 更新。
- 是否需要拆分种子仓任务、主仓任务和 Framework Hub 任务。
- `capability_map_update_status`
- `project_signal_update_status`
- `seed_repository_upgrade_suggestions`

## 禁区

- 不把真实 secret、客户隐私、生产日志、企业私有规则或未脱敏源码写入 Pack、Case Pack、export bundle、任务包或最终说明。
- 不把种子仓离线协议当成真实安装器。
- 不在用户未确认前写入 `.maw/mcp/registry.json`、`.maw/mcp/locks.json`、下载外部 zip、导入 bundle、发布资源或触发宿主机程序更新。
- 不把 Platform MCP / Local MCP 变成任意下载代理、localhost tunnel、shell/path/token/secret 绕行入口。
- 不把种子仓、主仓和 Framework Hub 的执行边界混成一个仓库内修改。

## 冲突与覆盖规则

- 用户本轮明确指令优先于 Pack 或 project override。
- Project override 高于 user/shared/official pack，但不能覆盖安全边界。
- strict lock 下 shared registry 更新不能自动影响项目。
- 与 `#MCP服务诊断` 冲突时，本指令负责知识运行时和 Pack；`#MCP服务诊断` 负责 endpoint、tools/list、ping 和授权拒绝边界。

## 更新记录

- 2026-07-02：创建，登记 MCP Knowledge Runtime v1.1 种子仓协议、离线 registry、Pack 示例和检查脚本。

