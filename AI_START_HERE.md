# AI Start Here

MAWflow Seed is an open source AI project navigation system and workdir assistant for local coding agents.
This AI workdir gives those tools a stable local starting point without replacing project facts or human review.

When Codex, Claude Code, Gemini CLI, Cursor Agent, or another local AI coding tool enters this project directory, start here before changing files.

## What This Directory Provides

Seed gives the AI:

- project facts in `.maw/project.yaml`;
- component boundaries in `.maw/components.yaml`;
- module boundaries in `.maw/modules.yaml`;
- runtime hints in `.maw/app-runtime.yaml`;
- collaboration rules in `.maw/agent-entry.yaml`;
- protected path and secret rules in `.maw/policies.yaml`;
- task and prompt structures under `prompts/`;
- validation and release checks under `ops/`.

Seed does not replace the user's IDE, project manager, cloud platform, or review process. It gives local AI tools a stable project map and execution contract.

## Startup Order

1. Read `AGENTS.md` if your tool supports it.
2. Read this file.
3. Read `.maw/agent-entry.yaml`.
4. Read `.maw/project.yaml`, `.maw/components.yaml`, `.maw/modules.yaml`, and `.maw/app-runtime.yaml`.
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
