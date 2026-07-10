# Security Policy

## Public Boundary

Mawflow Seed is a public project scaffold and AI Coding equipment pack. It must not include real credentials, customer data, private operational logs, production database URLs, SSH private keys, internal prompts, hidden workspaces, or Mawflow control-plane runtime code.

## Reporting

Report suspected vulnerabilities through GitHub Security Advisories on `https://github.com/mawflow/mawflow-seed/security/advisories`. Do not create a public issue containing secrets, exploit details, customer data, or production paths.

## Sanitization

Before sharing a reproduction or Prompt Case:

- remove project names, customer names, account names, tokens, cookies, URLs, local paths and logs;
- replace secrets with stable placeholders such as `<TOKEN>` or `<DB_URL>`;
- keep only the minimum structure needed to reproduce the issue;
- ask for maintainer confirmation before publishing.

## Release Gate

Formal public release uses the MIT `LICENSE`, `docs/public-seed/open-source-release.md`, source-only release gates, and the materialized-payload command `python3 ops/scripts/check-public-seed-workdir.py --format json --strict`. Before announcement, maintainers must still confirm the public repository visibility and release/tag policy.
