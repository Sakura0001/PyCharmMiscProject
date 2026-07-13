# Audit Lifecycle Plan

Audit lifecycle TSV rows as SQL object action chains.

Required checks:

- Each row has setup, target, verification, and cleanup intent.
- Actions are SQL lifecycle actions, not implementation pipeline stages.
- Target statements exist in `references/statements/`.
- Cleanup removes objects created by setup or target actions.
- MySQL 8.0.22 version-sensitive factors cite official sources.
