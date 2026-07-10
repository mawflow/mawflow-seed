# 指令：最近会话概要检索与写入

## 元信息

- ID：TINST-034
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/recent-session-briefs.md`
- 推荐调用：`#会话概要`
- 精确调用：`#T034` 或 `#T034/会话概要`
- 触发词：#会话概要、最近会话、会话摘要、任务概要、最近任务、读取最近几次会话、recent-session-briefs、session briefs、跨设备接力、短期记忆
- 适用范围：任务开始前判断最近几次 AI 会话是否相关；任务结束时写入可跨设备同步的任务概要；多电脑协同开发时恢复短期上下文。

## 目标

让 AI 在新任务开始时能先读到最近几次会话的轻量任务概要，判断有关联后再细读具体概要、任务包 `SESSION_STATE.md` 或相关文档。该能力避免每次全量翻聊天记录，也避免把本机私有信息写入共享文档。

## 输入要求

- 必需输入：当前任务关键词或用户当前请求；若缺失，使用用户最新消息、命中路径、命令或模块名作为 query。
- 可选输入：最近条数、检索范围、是否写入本轮概要、任务类型、能力 key、模块、app_key、提交 hash、验证命令。
- 缺失时处理：默认读取最近 8 条概要候选；没有历史概要时继续当前任务，不阻塞。

## 执行步骤

### 1. 任务开始时检索

1. 不全量读取 `docs/ai-session-briefs/**`。
2. 运行：

```bash
python3 ops/scripts/recent-session-briefs.py --recent 8 --query "<当前任务关键词>" --format markdown
```

3. 只在候选为 `high` 或 `medium` 相关时，读取候选概要全文。
4. 如果候选概要指向 `SESSION_STATE.md`，且本次任务要续做同一任务包，再读取该状态文件。
5. 如果概要与当前代码、`.maw`、模块档案、PM 源或用户最新说明冲突，以当前事实和用户最新说明为准。

### 2. 任务结束时判断是否写入

满足任一条件时，写入共享会话概要：

- 本轮产生了提交、升级资产、发布结果、审计报告或重要验证结论。
- 本轮做了模板协议、项目指令、能力地图、任务包、脚本或模块边界变更。
- 本轮任务很可能被下一台电脑、下一个 Codex 会话或派生项目模板升级接力。
- 用户明确要求“记录最近任务”“下次能接上”“会话概要”。

不写共享概要的情况：

- 纯闲聊、一次性问答、未产生项目事实。
- 只包含本机路径、端口、代理、账号、token、客户隐私或未脱敏日志。
- 内容更适合沉淀为稳定经验，应写入 `docs/ai-instructions/experience-index.md` 或候选台账。
- 内容只适合本机，应写入 `.local/ai/**` 或 `.local/maintenance/**`。

### 3. 写入概要

推荐使用脚本生成：

```bash
python3 ops/scripts/write-session-brief.py \
  --title "<任务标题>" \
  --status success \
  --task-type "<任务类型>" \
  --capability "<capability_key>" \
  --tag "<关键词>" \
  --summary "<一句话结果>"
```

脚本会写入：

```text
docs/ai-session-briefs/YYYY/MM/YYYYMMDD-HHMMSS-<slug>.md
```

写入后可人工补充“关键决策”“修改范围”“验证结果”“后续提示”。同一轮任务的概要应随本轮改动一起提交推送。

### 4. 多电脑协同

- 每个概要单独文件，不追加写同一个全局索引，降低 Git 冲突。
- 另一台电脑开始任务前，若工作流允许，先同步项目仓库，再运行检索脚本。
- 本机私有差异只写 `.local/**`，不要因为需要跨设备而把私密路径写进共享概要。

## 验证方式

最低验证：

```bash
git diff --check
python3 -m py_compile ops/scripts/recent-session-briefs.py
python3 -m py_compile ops/scripts/write-session-brief.py
python3 ops/scripts/recent-session-briefs.py --recent 8 --format json
python3 ops/scripts/extract-doc-index.py --scope docs/ai-session-briefs --format json
```

修改模板协议或能力登记时还应运行：

```bash
bash ops/scripts/check-template-module-docs.sh
bash ops/scripts/check-technical-map.sh
bash ops/scripts/check-ai-framework-consistency.sh
bash ops/scripts/check-local-boundary.sh
```

## 禁区

- 不全量读取 `docs/ai-session-briefs/**` 来建立上下文。
- 不把完整聊天记录、长日志或执行流水塞进概要。
- 不写真实密钥、token、账号密码、客户隐私、生产连接串、未脱敏日志或个人本机路径。
- 不把概要当作权威事实反向覆盖代码、`.maw` 或模块档案。
- 不用单个 `recent-sessions.md` 追加所有概要，避免多电脑协同时产生冲突。

## 冲突与覆盖规则

- 用户最新说明、当前代码、`.maw` 配置、模块档案和任务包 `SESSION_STATE.md` 优先于旧概要。
- 概要只提供“是否值得细读”的路线，不替代事实核对。
- 派生项目已有自己的会话记录规范时，保留项目规范，按字段映射增量兼容。

## 更新记录

- 2026-06-21：创建，新增最近会话概要检索与写入机制。
