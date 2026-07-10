# MAWflow Seed

MAWflow Seed is the open-source AI project navigation system for AI Coding workspaces.

It helps a regular code repository describe its project structure, module boundaries, execution rules, validation entry points, and delivery evidence, so tools such as Codex, Claude Code, Cursor, Gemini CLI, and other local agents can work with clearer project context.

Repository metadata and older release notes may use `Mawflow Seed`; this README uses the public product spelling `MAWflow Seed`.

中文简介：

MAWflow Seed 是安装在 AI 编程工作目录里的开源 AI 项目导航系统。它帮助普通代码仓库说清项目结构、模块关系、执行边界和验证入口，让 AI 编程工具能够在明确上下文和规则下参与真实软件项目。

## What is MAWflow Seed?

MAWflow Seed is not just a template and not just a demo repository.

It is a repository-level navigation layer for AI Coding projects. Seed is designed to help an AI coding tool answer these questions before changing files:

- What is this project?
- What are the main modules?
- Where should the agent start reading?
- What paths are allowed or protected?
- Which commands or checks prove the task is complete?
- What should be recorded for review, acceptance, and future handoff?

Seed provides a lightweight project structure and collaboration protocol so that AI work is easier to understand, execute, verify, and review.

## Why Seed?

AI coding tools can generate code, but real software projects require more than code generation.

A project usually needs:

- project goals;
- module boundaries;
- technical context;
- task constraints;
- validation commands;
- security boundaries;
- human review;
- delivery evidence.

Without a clear project navigation layer, each AI session has to rediscover the repository, guess module ownership, and infer validation rules from scattered files or chat history.

Seed helps move AI Coding from one-off conversations into a manageable project workflow.

## What Seed helps with

| Need | Seed helps by |
| --- | --- |
| Make the project understandable to AI | Describing project identity, structure, modules, and runtime hints. |
| Reduce context confusion | Providing agent entry files and module navigation. |
| Control execution scope | Defining allowed paths, protected paths, and task boundaries. |
| Make tasks executable | Using Prompt Spec and Task Pack style task descriptions. |
| Make results verifiable | Recording checks, validation results, and review notes. |
| Keep project knowledge reusable | Preserving project facts, decisions, and experience in repository files. |
| Prepare for public sharing | Separating public examples from private data, local-only files, and credential material. |

## How Seed fits into MAWflow

MAWflow is an AI project execution system.

Seed is the open-source starting point in the MAWflow product path:

```text
Project Clinic
Project goal clarification

Prompt Hub
Structured requirement expression

Seed
AI project navigation system

Host Base
Local technical runtime base

Project Space
Business project execution base

Studio / Enterprise
Team project workspace: cloud collaboration / private deployment
```

### Seed

Seed establishes project navigation inside the repository.

It helps AI tools understand project structure, module relationships, execution boundaries, and validation entry points.

### Host Base

Host Base provides the local technical runtime for MAWflow, including CLI, local runtime, login activation, plugins, and local capability connection.

### Project Space

Project Space organizes project goals, requirements, work items, AI execution records, human confirmation, acceptance results, and delivery evidence.

### Studio / Enterprise

Studio and Enterprise are two delivery forms of the MAWflow team project workspace.

- Studio is the cloud collaboration workspace for one-person companies, small teams, and delivery teams.
- Enterprise is the private deployment and governance-enhanced form of Studio for enterprise customers.

Enterprise is not a separate product path unrelated to Studio. It reuses the same Project Space execution model and enhances deployment, permissions, audit, model governance, credential governance, release approval, and system integration.

## Current status

This repository is the public open-source starting point for MAWflow Seed.

The current release line includes:

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

These files provide:

- AI workdir entry rules;
- project identity and module maps;
- task and prompt specifications;
- validation and readiness checks;
- delivery evidence examples;
- public sharing and redaction boundaries.

Always check the repository contents and release notes before assuming a specific file, command, or product capability is available.

## Quick start

Clone the public Seed repository:

```bash
git clone https://github.com/mawflow/mawflow-seed.git my-project
cd my-project
```

If you already use MAWflow CLI, the recommended project creation path is:

```bash
mawflow project init my-project
cd my-project
```

Then update the generated project facts:

```text
README.md
AI_START_HERE.md
.maw/project.yaml
.maw/components.yaml
.maw/modules.yaml
.maw/app-runtime.yaml
```

For an existing repository, do not overwrite your codebase with Seed files. Adopt Seed incrementally:

1. Create or switch to a safe Git branch.
2. Add `.maw/` project facts.
3. Add AI entry files such as `AI_START_HERE.md`.
4. Add module and runtime information.
5. Add validation and review notes.
6. Keep private data, local-only files, and credential material out of Git.

When Seed becomes your own project workspace, rewrite the project README around your real product or service. `TEMPLATE_OVERVIEW.md` explains the Seed repository internals for maintainers.

For step-by-step setup, see `GETTING_STARTED.md`.

## Repository structure

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

Actual files may differ by release version. Follow the current repository contents, `TEMPLATE_VERSION`, and `CHANGELOG.md`.

## What Seed is not

MAWflow Seed is not:

- a full cloud platform;
- a project management SaaS;
- an AI account pool;
- a credential management service;
- a private deployment package;
- a replacement for human review;
- a tool that lets AI bypass approval and deploy to production.

Seed does not provide Enterprise governance, centralized permissions, model billing, private deployment, or cloud Project Space by itself.

For local runtime, project workspace, team collaboration, or private deployment, continue with MAWflow Host Base, Lite, Studio, or Enterprise.

## Upgrade path

You can start with Seed and move forward when the project needs more structure:

| Need | Next step |
| --- | --- |
| Local runtime, login activation, plugins | Host Base |
| Existing local project enhancement | Lite |
| Team project collaboration and delivery evidence | Studio |
| Enterprise private deployment and governance | Enterprise |
| AI usage planning and model boundaries | AI Access / AI Credits |
| Independent review and delivery audit | Audit Center |

## Public and private boundaries

Do not commit:

```text
.local/
.maw/*.local.yaml
real credentials
access keys
login credentials
private key files
production connection details
customer private data
raw logs with sensitive data
```

Seed is designed to make AI collaboration clearer, not to expose private project data.

## Learn more

- MAWflow official site: <https://ai.mawflow.com>
- Seed manual: <https://ai.mawflow.com/seed/>
- Quick start: <https://ai.mawflow.com/docs/quickstart>
- Product features: <https://ai.mawflow.com/docs/product-features>
- Trust Center: <https://ai.mawflow.com/docs/trust-center>

## Useful entry points

- `docs/public-seed/README.md`
- `docs/public-seed/quickstart.md`
- `docs/public-seed/prompt-spec.md`
- `docs/public-seed/pack-types.md`
- `docs/public-seed/desensitization.md`
- `docs/public-seed/open-source-release.md`
- `GETTING_STARTED.md`
- `PROJECT_COMMANDS.md`
- `CHATGPT_TO_CODEX.md`
- `TEMPLATE_OVERVIEW.md`

## Contact

For general questions, business cooperation, Studio, Enterprise, or private deployment:

```text
hello@mawflow.com
```

For product support, installation issues, account activation, Seed usage, Host Base, Lite, Studio usage, privacy, security, or data requests:

```text
support@mawflow.com
```

## License

MAWflow Seed is released under the MIT License. See `LICENSE`.
