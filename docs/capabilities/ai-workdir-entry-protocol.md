# AI 工作目录入口协议

capability_key: `ai-workdir-entry-protocol`
signal_id: `SIG-20260709-ai-workdir-entry-protocol`

## Summary

Mawflow Seed provides a shared entry protocol for local AI coding tools working inside a project directory. The protocol gives agents a stable boot path, project facts, protected boundaries, validation expectations, and closeout rules before they edit code.

## Files

- `AI_START_HERE.md`: human-readable starting point for any AI tool.
- `.maw/agent-entry.yaml`: canonical machine-readable entry contract.
- `.maw/agent-rules.yaml`: shared rule set for tool-specific adapters.
- `AGENTS.md`: Codex and CLI Agent adapter aligned to the shared entry contract.

Future adapters such as `CLAUDE.md`, `GEMINI.md`, and `.cursor/rules/mawflow.md` should be generated from or checked against `.maw/agent-entry.yaml`.

## Boundaries

The entry protocol is not a runtime service, IDE plugin, cloud platform, or project management system. It is a directory-level contract that helps AI tools understand what to read, what to avoid, how to scope work, how to validate, and how to report completion.

## Validation

Seed distribution and public release checks should confirm that the entry protocol exists and that public-facing copy does not expose internal repository URLs, local paths, private prompts, or real secrets.
