---
doc_key: docs.capabilities.agent_skill_integration
doc_type: capability
stage: governance
status: active
owner: planner
tags:
  - agent-skill
  - seed
  - discovery
read_contract:
  summary: "Mawflow Agent Skills 与 Seed 项目规则之间的可选发现、适配和兼容边界。"
  ai_read_hint: "实现、安装、升级或审查 Mawflow Agent Skill，以及验证无 Skill 降级时读取。"
---

# Mawflow Agent Skill 集成

## 定位

Mawflow Agent Skills 是面向 Codex、Claude Code、Gemini CLI、Cursor Agent 等本地 Agent 的可选用户级扩展，负责：

- 发现 MAWflow 项目和入口文件；
- 把自然语言意图路由到 `mawflow` CLI 或 Local MCP；
- 在执行前展示计划、风险与确认要求；
- 为不同 Agent 提供一致的薄适配层。

Skill 不保存项目规则，不复制 Seed 指令正文，不参与项目运行，也不是安装 MAWflow 的前置条件。

## 权威顺序

```text
用户当前明确要求
-> 当前项目 AGENTS.md / AI_START_HERE.md / .maw / PROJECT_COMMANDS.md
-> Mawflow Agent Skill
-> Agent 默认行为
```

冲突时保留双方安全限制，以项目事实为准；Skill 只能提示兼容差异，不自动改写项目。

## 安装方式

推荐使用用户级安装，不把 Skill 目录提交到业务项目。当前统一安装入口采用自然语言计划：

```text
请阅读 https://ai.mawflow.com/manuals/agent-skills.html，按照步骤为我安装并配置 Mawflow Agent Skill。

要求：
1. 检查当前 Agent 类型和用户级 Skill 目录。
2. 检查 Mawflow CLI 与当前项目 Seed 入口。
3. 只生成安装计划，不立即写入。
4. 获得用户确认后执行用户级安装。
5. 安装后运行发现、CLI 适配和无 Skill 降级验证。
6. 不修改当前项目文件，不复制项目规则或敏感信息。
```

在统一 Skill 分发包正式发布前，安装器必须显示 `distribution_pending`，不能从未知 URL 或未经确认的本机目录复制。后续 CLI 入口保持 `plan -> confirm -> execute`：

```text
mawflow skills list
mawflow skills install --plan
mawflow skills install --execute
mawflow skills doctor
mawflow skills update
```

这些命令是兼容契约；未在当前 CLI 版本提供时应明确提示“尚未发布”，不能伪造成功。

## 使用方式

Agent 发现 Skill 后应先检查当前目录：

1. 查找 `AI_START_HERE.md` 和 `.maw/agent-entry.yaml`。
2. 读取 `external_agent_skills.mawflow`，确认 `required: false`。
3. 按项目 `startup.recommended_order` 建立上下文。
4. 只把用户意图转换为现有 CLI/MCP/项目指令入口。
5. 高风险交付、发布和镜像同步默认关闭，必须展示计划并获得确认。

建议产品分包保持四个职责：`mawflow-host`、`mawflow-project`、`mawflow-workflow`、`mawflow-delivery`。其中 delivery 默认禁用，不因安装 Skill 自动开放。

## 无 Skill 降级

- 从未安装：直接从 `AI_START_HERE.md` 启动，全部项目能力可用。
- 暂时禁用：不改变项目文件、CLI 配置或运行结果。
- 已卸载：Seed doctor、项目开发、验证和交付继续工作。
- Skill 调用失败：回退到项目入口并报告失败，不猜测项目规则。

`ops/scripts/check-agent-skill-integration.py` 在仓库没有项目级 Mawflow Skill 副本的前提下验证入口完整性，作为“无 Skill”基线证据。`installed` 与 `old` 场景默认临时生成符合独立 `mawflow-skills` 目录约定的 bundle manifest 和四个最小 `SKILL.md`，实际读取后再验证项目入口；检查结束即删除，不会把 Skill 复制进项目。正式分发候选可用 `--skill-root <mawflow-skills目录>` 替换一次性探针。

## 版本兼容

- Seed 通过 `.maw/agent-entry.yaml` 声明当前兼容契约；Skill 读取声明，不反向覆盖。
- 旧 Skill 不认识新字段时必须忽略未知字段并继续读取项目入口。
- Skill 自身协议版本低于项目要求时提示 `skill_compatibility_warning`，继续使用项目文件，不自动升级或修改项目。
- 新 Skill 面对旧 Seed 时只提供发现与只读建议；缺少安全边界或写入契约时禁止高风险动作。
- 任何升级都保留“未安装 Skill”路径，并通过无 Skill、有 Skill、卸载、旧版本四组测试。

## 安全边界

Skill 不得包含完整 `PROJECT_COMMANDS.md`、完整项目规则、当前模块清单、客户信息、发布账号、token、密钥或生产连接串。Skill 只保存通用路由、调用方法、安全边界和项目入口读取方式。

## 验证

```bash
python3 ops/scripts/check-agent-skill-integration.py --format json
python3 ops/scripts/check-agent-skill-integration.py --scenario installed --format json
python3 ops/scripts/check-agent-skill-integration.py --scenario uninstalled --format json
python3 ops/scripts/check-agent-skill-integration.py --scenario old --format json
python3 ops/scripts/check-agent-skill-integration.py --scenario installed --skill-root <mawflow-skills目录> --format json
bash ops/scripts/check-ai-framework-consistency.sh
bash ops/scripts/check-local-boundary.sh
```
