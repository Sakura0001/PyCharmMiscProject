# Statement Combination Matrices

This directory contains machine-readable statement combination matrices.

Statement references under `references/statements/**/*.md` define factors,
factor values, tiers, rendering hints, and coverage policy. Combination
matrices under this directory define which factor bindings are required
baseline SQL combinations.

Rules:

- Required baseline coverage must pass before AI or runner derived extensions
  are generated.
- Derived extensions are allowed after baseline audit passes, but must be
  written to `artifacts/intermediates/<task_slug>/derived_extension_combinations.yaml`.
- Derived extensions must not satisfy required factor, relation, table, or
  column-type coverage.
- Every expected failure must have a stable reason.
- Every matrix must explicitly declare whether relation, table, and column
  type coverage are required.
