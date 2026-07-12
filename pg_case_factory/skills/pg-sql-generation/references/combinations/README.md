# Statement Combination Matrices

This directory contains machine-readable statement combination matrices.

Statement references under `references/statements/**/*.md` define factors,
factor values, tiers, rendering hints, and coverage policy. Combination
matrices under this directory define which factor bindings are required
baseline SQL combinations.

Rules:

- Required baseline coverage must pass before AI or runner derived extensions
  are generated.
- Every matrix must contain a machine-readable
  `post_coverage_extension_policy` block. The runner must use that block
  instead of prose when deciding whether derived extensions are allowed.
- Derived extensions are allowed after baseline audit passes, but must be
  written to `artifacts/intermediates/<task_slug>/derived_extension_combinations.yaml`.
- Derived extensions must not satisfy required factor, relation, table, or
  column-type coverage.
- Every expected failure must have a stable reason.
- Every matrix must explicitly declare whether target object, relation, table,
  and column-type coverage are required.
- `coverage_mode: representative` or `conditional` is an honest legacy
  capability marker, not exhaustive evidence. A feature workflow must add a
  complete inventory axis and may not count such a scope toward `missing=0`.
- `all_pg18_column_types` is a deprecated name for only the 85 portable core
  profiles and can never prove exhaustive column coverage. An exhaustive claim
  must enumerate all seven canonical selectors in `pg18_type_catalog.md` and
  contain a direct `mode: exhaustive` baseline expansion for every selector.
- An exhaustive object or relation scope must use the canonical PG18.4 source
  selector, declare a set exactly equal to it, and expand that exact set. The
  legacy flat `table_kinds` selector is not canonical; complete table scope is
  instead the five-dimensional feature-plan inventory.
- The shipped 183 statement matrices currently contain **0 validated exhaustive
  scope claims**. Their profile/table scopes are conditional, representative,
  or explicit static declarations; they do not prove rendered SQL or runtime
  execution. The feature workflow must close those gaps obligation by obligation.
- Run `tools/audit_combination_matrix.py`; treat its partial-scope warnings as
  required feature-plan work, not as ignorable sampling permission.
