# MAWflow Seed

MAWflow Seed 是安装在 AI 编程工作目录中的开源 AI Coding 项目导航系统。

它帮助普通代码仓库清晰描述项目结构、模块边界、执行规则、验证入口和交付证据，让 Codex、Claude Code、Cursor、Gemini CLI 等本地 AI 编程工具能够在明确的项目上下文和约束下参与真实软件研发。

仓库元数据和历史版本说明中可能使用 `Mawflow Seed`，本文统一使用公开产品名称 `MAWflow Seed`。

## MAWflow Seed 是什么

MAWflow Seed 不只是一个项目模板，也不只是一个演示仓库。

它是面向 AI 编程项目的仓库级导航层，用于帮助 AI 工具在修改文件前回答这些问题：

- 这是什么项目？
- 项目包含哪些主要模块？
- AI 应该从哪里开始读取？
- 哪些路径允许修改，哪些路径受到保护？
- 哪些命令和检查可以证明任务已经完成？
- 哪些结果需要记录，供评审、验收和后续交接使用？

Seed 提供轻量的项目结构和协作协议，让 AI 研发工作更容易理解、执行、验证和评审。

## 为什么需要 Seed

AI 编程工具可以生成代码，但真实软件项目需要的不只是代码生成。

一个可持续维护的项目通常还需要：

- 明确的项目目标；
- 清晰的模块边界；
- 可追溯的技术上下文；
- 可执行的任务约束；
- 可复现的验证命令；
- 必要的安全边界；
- 人工评审与确认；
- 可审计的交付证据。

如果缺少清晰的项目导航层，每次 AI 会话都需要重新发现仓库结构、猜测模块归属，并从分散的文件或聊天记录中推断验证规则。

Seed 帮助 AI 编程从一次性对话走向可管理、可验证、可持续的项目工作流。

## Seed 能解决什么问题

| 项目需求 | Seed 提供的帮助 |
| --- | --- |
| 让 AI 理解项目 | 描述项目身份、目录结构、模块关系和运行提示 |
| 减少上下文混乱 | 提供统一的 AI 入口文件和模块导航 |
| 控制执行范围 | 定义允许路径、保护路径和任务边界 |
| 让任务可以执行 | 使用提示词规范和任务包描述具体工作 |
| 让结果可以验证 | 记录检查命令、验证结果和评审结论 |
| 让项目知识可以复用 | 在仓库内保留项目事实、决策和经验 |
| 为开源发布做准备 | 区分公开示例、私有数据、本机文件和凭证材料 |

## Seed 在 MAWflow 中的位置

MAWflow 是一套 AI 项目执行系统。

Seed 是 MAWflow 产品路径中的开源起点：

```text
Project Clinic
项目目标澄清

Prompt Hub
结构化需求表达

Seed
AI 项目导航系统

Host Base
本地技术运行基础

Project Space
业务项目执行空间

Studio / Enterprise
团队项目工作空间：云端协作 / 私有部署
```

### Seed

Seed 在代码仓库内建立项目导航，帮助 AI 工具理解项目结构、模块关系、执行边界和验证入口。

### Host Base

Host Base 提供 MAWflow 的本地技术运行环境，包括命令行工具、本地运行时、登录激活、插件和本地能力连接。

### Project Space

Project Space 用于组织项目目标、需求、工作项、AI 执行记录、人工确认、验收结果和交付证据。

### Studio / Enterprise

Studio 和 Enterprise 是 MAWflow 团队项目工作空间的两种交付形态。

- Studio 面向一人公司、小型团队和交付团队，提供云端协作工作空间。
- Enterprise 是 Studio 的私有部署和治理增强形态，面向企业客户。

Enterprise 不是一条与 Studio 无关的独立产品路径。它复用相同的 Project Space 执行模型，并增强部署、权限、审计、模型治理、凭证治理、发布审批和系统集成能力。

## 当前状态

本仓库是 MAWflow Seed 的公开开源入口。

当前版本包含以下核心结构：

```text
AI_START_HERE.md
AGENTS.md
.maw/
docs/
prompts/
ops/
code/server/
code/client/
LICENSE
```

这些文件用于提供：

- AI 工作目录入口规则；
- 项目身份和模块地图；
- 任务与提示词规范；
- 验证和就绪检查；
- 交付证据示例；
- 公开发布和脱敏边界。

在使用某项文件、命令或产品能力前，请以当前仓库内容、`TEMPLATE_VERSION` 和 `CHANGELOG.md` 为准。

## 快速开始

克隆公开 Seed 仓库：

```bash
git clone https://github.com/mawflow/mawflow-seed.git my-project
cd my-project
```

如果已经安装 MAWflow CLI，推荐使用项目初始化命令：

```bash
mawflow project init my-project
cd my-project
```

然后更新生成项目中的真实项目信息：

```text
README.md
AI_START_HERE.md
.maw/project.yaml
.maw/components.yaml
.maw/modules.yaml
.maw/app-runtime.yaml
```

如果要在已有仓库中引入 Seed，不要使用 Seed 文件整包覆盖现有代码，应采用增量方式接入：

1. 创建或切换到安全的 Git 分支。
2. 增加 `.maw/` 项目事实配置。
3. 增加 `AI_START_HERE.md` 等 AI 入口文件。
4. 补充模块和运行时信息。
5. 增加验证记录和评审说明。
6. 确保私有数据、本机文件和凭证材料不进入 Git。

当 Seed 被用于创建真实项目后，应根据实际产品或服务重写项目 `README.md`。维护者可以通过 `TEMPLATE_OVERVIEW.md` 了解 Seed 仓库自身的内部结构。

完整安装步骤请阅读 `GETTING_STARTED.md`，常用项目命令和维护入口请阅读 `PROJECT_COMMANDS.md`，从外部 AI 向 Codex 交接任务请阅读 `CHATGPT_TO_CODEX.md`。

## 仓库结构

```text
.
├── README.md
├── AI_START_HERE.md
├── AGENTS.md
├── LICENSE
├── .maw/
│   ├── project.yaml
│   ├── components.yaml
│   ├── modules.yaml
│   ├── app-runtime.yaml
│   └── agent-entry.yaml
├── code/
│   ├── server/
│   └── client/
├── docs/
│   ├── README.md
│   ├── public-seed/
│   ├── modules/
│   └── ai-instructions/
├── prompts/
│   └── codex/
└── ops/
    └── scripts/
```

不同版本的实际文件可能存在差异，请以当前仓库内容、`TEMPLATE_VERSION` 和 `CHANGELOG.md` 为准。

## Seed 不是什么

MAWflow Seed 不是：

- 完整的云平台；
- 项目管理软件即服务；
- AI 账号池；
- 凭证管理服务；
- 私有部署安装包；
- 人工评审的替代品；
- 允许 AI 绕过审批并直接部署生产环境的工具。

Seed 本身不提供 Enterprise 治理、集中权限、模型计费、私有部署或云端 Project Space。

如果需要本地运行环境、项目工作空间、团队协作或私有部署，可以继续使用 MAWflow Host Base、Lite、Studio 或 Enterprise。

## 升级路径

可以从 Seed 开始，并在项目需要更多结构和能力时继续升级：

| 项目需求 | 下一步 |
| --- | --- |
| 本地运行环境、登录激活和插件 | Host Base |
| 增强已有本地项目 | Lite |
| 团队项目协作和交付证据 | Studio |
| 企业私有部署和治理 | Enterprise |
| AI 使用规划和模型边界 | AI Access / AI Credits |
| 独立评审和交付审计 | Audit Center |

## 公开与私有边界

不要提交以下内容：

```text
.local/
.maw/*.local.yaml
真实凭证
访问密钥
登录凭证
私钥文件
生产连接信息
客户私有数据
包含敏感信息的原始日志
```

Seed 的目标是让 AI 协作更清晰，而不是暴露项目的私有数据。

## 许可证

MAWflow Seed 使用 MIT License，具体内容见 `LICENSE`。

## 了解更多

- MAWflow 官方网站：<https://ai.mawflow.com>
- Seed 使用手册：<https://ai.mawflow.com/seed/>
- 快速开始：<https://ai.mawflow.com/docs/quickstart>
- 产品能力：<https://ai.mawflow.com/docs/product-features>
- 信任中心：<https://ai.mawflow.com/docs/trust-center>
