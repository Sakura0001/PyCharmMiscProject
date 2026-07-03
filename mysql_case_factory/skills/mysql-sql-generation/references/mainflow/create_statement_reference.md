# Create Statement Reference

Create or complete a MySQL statement reference at
`references/statements/<category>/<domain>/<statement_key>.md`.

Requirements:

- Include at least one official MySQL URL.
- State whether the source is proven for MySQL 8.0.22.
- Put all machine-readable content in a fenced `yaml` block under
  `structured_config`.
- Define factors, coverage policy, defaults, and rendering.
- For PostgreSQL-derived factors, record whether each factor is retained,
  rewritten, dropped, or pending review in migration docs.
