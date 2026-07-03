# Generate SQL From Request

Use this workflow to convert a natural-language MySQL 8.0.22 request into a
lifecycle plan, an optional generation program, and SQL files.

1. Discover bundled object templates from `assets/objects/**/*.sql`.
2. Discover statement references from `references/statements/**/*.md`.
3. Match exactly one base object candidate and one statement candidate.
4. Read the matched statement reference plus needed common rules.
5. Write a lifecycle TSV under `artifacts/test_plans/`.
6. Prefer a matching combination matrix when it exists.
7. Generate SQL through the generic Python engine; do not hard-code statement
   behavior in `src/mysql_case_factory`.

All statement semantics must be traceable to MySQL Community Server 8.0.22
official documentation.
