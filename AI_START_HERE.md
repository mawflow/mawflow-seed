# AI Start Here

MAWflow Seed is an open source AI project navigation system and workdir assistant for local coding agents.
This AI workdir gives those tools a stable local starting point without replacing project facts or human review.

When Codex, Claude Code, Gemini CLI, Cursor Agent, or another local AI coding tool enters this project directory, start here before changing files.

## What This Directory Provides

Seed gives the AI:

- project facts in `.maw/project.yaml`;
- subproject boundaries in `.maw/subprojects.yaml`;
- shared Git declarations in `.maw/code-sources.yaml`, deployment targets in `.maw/deployments.yaml`, and component boundaries in `.maw/components.yaml`;
- module boundaries in `.maw/modules.yaml`;
- runtime hints in `.maw/app-runtime.yaml`;
- collaboration rules in `.maw/agent-entry.yaml`;
- protected path and secret rules in `.maw/policies.yaml`;
- task and prompt structures under `prompts/`;
- validation and release checks under `ops/`.

Seed does not replace the user's IDE, project manager, cloud platform, or review process. It gives local AI tools a stable project map and execution contract.

## Optional Agent Skill

Mawflow Agent Skills may be installed at user scope to help an Agent discover this directory and adapt natural-language requests to the `mawflow` CLI or Local MCP. The Skill is optional: when it is absent, disabled, uninstalled, or older than this Seed, continue with the project-local startup order below. A Skill never replaces project files, never overrides project facts, and never becomes a prerequisite for development or validation.

## Startup Order

1. Read `AGENTS.md` if your tool supports it.
2. Read this file.
3. Read `.maw/agent-entry.yaml`.
4. Read `.maw/project.yaml`, `.maw/subprojects.yaml`, `.maw/code-sources.yaml`, `.maw/deployments.yaml`, `.maw/components.yaml`, `.maw/modules.yaml`, and `.maw/app-runtime.yaml`.
5. Read `docs/README.md` and then only the docs needed for the current task.
6. Locate the module or component before editing.
7. State the intended scope and validation path before broad changes.

## Default Boundaries

- Do not modify unrelated modules.
- Do not copy template defaults over real project facts.
- Do not commit `.local/**`, real secrets, tokens, private keys, production connection strings, raw logs, build output, or user-uploaded files.
- Do not read `prompts/**`, `runtime/**`, `workspaces/**`, `artifacts/**`, or `docs/archive/**` unless the user explicitly points to them or the active task directly requires them.

## Completion Contract

At the end of a task, report:

- what changed;
- what was verified;
- what was not verified and why;
- known risks;
- release or local environment impact;
- suggested next step when a human decision is needed.
