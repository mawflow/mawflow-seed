# Mawflow Seed Open Source Release

Mawflow Seed is released as an open source AI Coding equipment pack under the MIT License.

## Public Release Target

- Public remote: `https://github.com/mawflow/mawflow-seed`
- Release branch: `main`
- License: MIT, see `LICENSE`

The public remote is the distribution target for the Seed equipment pack. It does not grant access to the Mawflow control plane, Studio Cloud, Enterprise governance services, customer data, hidden workspaces, production secrets, or internal runtime infrastructure.

## Release Boundary

The public repository may include:

- `.maw` collaboration protocol templates and examples.
- `.maw/template-source.example.yaml` as a public-safe source-channel example.
- Public task-pack templates and Prompt Spec docs.
- Public checks for module dossiers, local boundary, distribution readiness, and open-source readiness.
- Public documentation under `docs/public-seed/`.
- Example Prompt Pack, Task Pack, Check Pack, and Verification Pack assets.

The public repository must not include:

- Real credentials, `.env` values, SSH private keys, API keys, tokens, production connection strings, or unredacted logs.
- The private development source file `.maw/template-source.yaml`; public users may copy `.maw/template-source.example.yaml` when they need a project-local source declaration.
- Customer project data, private task records, internal prompts, hidden workspaces, or proprietary control-plane runtime code.
- Main-repo Orchestrator, Workbench, Governance Admin, Platform MCP, HostCommand, ActionRun, Approval, Secret Governance runtime, or Enterprise-only implementation.

## Formal Release Checklist

1. `LICENSE` exists and matches MIT.
2. `TEMPLATE_VERSION` equals `vX.Y.Z`.
3. `CHANGELOG.md` mentions `vX.Y.Z`.
4. `.maw-template/public-release-profile.yaml` declares `profile_key: mawflow_seed_public_v1`.
5. Source branch is `release/vX.Y.Z`.
6. Source tag `vX.Y.Z` points at source HEAD.
7. `bash ops/scripts/check-seed-open-source-readiness.sh --strict --format json` returns `status=ready`.
8. `bash ops/scripts/check-seed-distribution-readiness.sh --strict --format json` passes.
9. `bash ops/scripts/check-local-boundary.sh` passes.
10. `bash ops/scripts/check-code-deliverable.sh` passes.
11. The MultiAgentWorker main repository `public_seed` plan confirms the target public repository is `https://github.com/mawflow/mawflow-seed` and reads the release profile.
12. The public payload gate reports `template_source_exported=false`, `internal_keyword_hits=0`, and `secret_pattern_hits=0`.
13. The materialized payload contains every path in `PUBLIC_PAYLOAD_MANIFEST.json` and passes `python3 ops/scripts/check-public-seed-workdir.py --format json --strict` inside the payload directory.
14. Public release must be executed from the main repository via `repository_publish_mirrors`, not by ad-hoc push from this seed development checkout.
