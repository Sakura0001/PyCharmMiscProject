---
name: regress-output-script-style
description: Use when generating, reviewing, renaming, or normalizing SQL regress case files whose filenames and SQL object names must share a stable numbered prefix.
---

# Regress Output Script Style

## Overview

Use this skill for SQL regress case files that must be stable in CI, easy to trace, and safe to rerun. The core rule is that every SQL file gets a canonical numbered filename, and every table or view defined or referenced inside that file must be tied to that filename.

This skill includes a validator script:

```bash
python3 skills/regress-output-script-style/scripts/validate_regress_sql_style.py <sql_dir> --prefix <prefix>
```

## When to Use

Use this skill when the user asks to:

- generate SQL regress cases;
- normalize or rename SQL files in the current directory;
- convert files to a shared prefix plus `001`, `002`, `003` sequence;
- make table names or view names match SQL filenames;
- review SQL regress output style, cleanup, determinism, or object naming.

Do not use it for non-SQL files, recursive project-wide renames, or PostgreSQL parser rewrites unless the user explicitly requests that broader scope.

## Filename Rule

The current directory's SQL files must be named:

```text
<prefix><NNN>.sql
```

Examples:

```text
A001.sql
A002.sql
A003.sql
A004.sql
```

Rules:

- `<prefix>` is a shared public prefix. Use the user-provided prefix.
- If no prefix is provided, ask for it before renaming files.
- `<NNN>` starts at `001` and increments by one.
- Default scope is only `.sql` files directly in the current directory, not subdirectories.
- Assign numbers by stable lexicographic order of the original filenames unless the user gives another order.
- If there are more than 999 SQL files, widen the number to four digits, such as `A0001.sql`.

## Object Naming Rule

Each SQL file determines the object prefix used inside that file.

```text
<prefix><NNN>.sql -> <prefix>_<NNN>_
```

Examples:

```text
A001.sql -> A_001_
A002.sql -> A_002_
IDX017.sql -> IDX_017_
```

Tables and views inside a file must start with that derived prefix:

```sql
CREATE TABLE A_001_base_table (...);
CREATE VIEW A_001_result_view AS ...;
```

Apply the same prefix to auxiliary objects when practical:

```text
A_001_idx_base_col
A_001_func_prepare_data
A_001_proc_load_data
A_001_type_status
```

If PostgreSQL unquoted identifier folding matters, prefer lowercase object names in the actual SQL while keeping the same relationship:

```text
A001.sql -> a_001_base_table
```

Do not mix objects from different file prefixes in one SQL file unless the test explicitly validates cross-object behavior and all dependencies are cleaned up.

## Complete Script Rule

Generated SQL must be a complete test script, not a bare statement. Each file should contain:

- header comment;
- session-level settings only, when needed;
- pre-cleanup;
- object setup;
- data setup;
- target statement;
- verification;
- final cleanup.

Use this order:

```text
header
session settings
pre-cleanup
create objects
insert or prepare data
target SQL
verification SQL
final cleanup
```

## Header Rule

Use a stable header:

```sql
-- --------------------------------------------------------
-- author       : codex
-- create at    : <YYYY-MM-DD>
-- description  : <what this case verifies>
-- FE           : <FE id, empty if none>
-- --------------------------------------------------------
```

The description must describe the actual behavior under test. Do not use generic filler text.

## Determinism and Cleanup

- Every case must be rerunnable.
- Pre-cleanup and final cleanup must be idempotent.
- Prefer `IF EXISTS`.
- Drop dependent objects before parent objects.
- Do not depend on business objects that already exist in the database.
- Do not use instance-level or persistent settings.
- Use session-level settings only when needed.
- Avoid unstable output such as timestamps, randomized row order, volatile plans, or environment-specific paths.
- Verification queries must use deterministic ordering when row order matters.
- Use `EXPLAIN` only when output is stable or intentionally filtered.

## Success and Failure Cases

- A success case must verify that the target object exists, the target property changed, or the behavior is observable.
- A failure case must have one clear failure reason.
- Mark expected failures in comments when needed.
- Do not combine unrelated failure causes in one file.
- Prefer one judgment per SQL file.

## Normalization Workflow

When applying this skill to the current directory:

1. List direct child `.sql` files in the current directory.
2. Confirm or obtain the shared filename prefix.
3. Sort files by original filename unless the user specified an order.
4. Build a dry-run mapping:

```text
old_case.sql -> A001.sql -> A_001_
another_case.sql -> A002.sql -> A_002_
```

5. Check for target filename collisions.
6. Check whether two files would produce the same SQL object name.
7. Rewrite table and view identifiers so definitions and references use the derived prefix.
8. Rewrite auxiliary object identifiers when doing so is needed for uniqueness or cleanup.
9. Rename files using a two-phase rename if any target name overlaps an existing source name.
10. Run the validator script against the directory.
11. Report the final mapping, object prefixes used, and validation result.

If the user asks for a preview, stop after the dry-run mapping and proposed content changes. If the user asks to apply the skill, perform the safe rewrite after collision checks.

## Mandatory Post-Run Validation

After generating, renaming, or normalizing SQL files with this skill, always run:

```bash
python3 skills/regress-output-script-style/scripts/validate_regress_sql_style.py <sql_dir> --prefix <prefix>
```

Validation checks:

- direct child `.sql` files use the expected `<prefix><NNN>.sql` sequence;
- numbering is contiguous from `001`;
- table and view definitions use the object prefix derived from the filename;
- table and view references in common DDL and DML clauses use the same derived prefix;
- the same object name does not appear across multiple SQL files without review.

If validation prints `PASS`, the directory satisfies the mechanical requirements enforced by the script.

If validation prints `MANUAL_CONFIRMATION_REQUIRED`, stop and show the report to the user. Do not silently accept or fix the mismatch. Ask the user to confirm whether each violation is intentional, caused by a parser limitation, or should be corrected. Continue only after that confirmation.

The validator is intentionally conservative. A manual confirmation is required for ambiguous cases such as cross-file dependencies, dynamic SQL, intentionally shared setup objects, or SQL constructs the script cannot safely classify.

## SQL Rewrite Guidelines

Prefer structured or syntax-aware edits when available. If editing text directly, be conservative:

- Rewrite object names in `CREATE TABLE`, `DROP TABLE`, `ALTER TABLE`, `INSERT INTO`, `UPDATE`, `DELETE FROM`, `TRUNCATE`, `FROM`, and `JOIN`.
- Rewrite view names in `CREATE VIEW`, `DROP VIEW`, `ALTER VIEW`, `FROM`, and `JOIN`.
- Keep definition and reference names consistent in the same file.
- Do not replace text inside ordinary string literals unless it is clearly dynamic SQL that references the object.
- Comments may be updated for clarity, but comments alone are not sufficient.
- Preserve unrelated SQL formatting and behavior.

## Safety Rules

- Do not overwrite an existing file.
- Do not silently skip a SQL file.
- Do not silently leave table or view names detached from the filename prefix.
- Do not rename recursively unless the user requested recursion.
- Do not make broad semantic SQL changes while normalizing names.
- If object ownership is ambiguous, report the ambiguity and show the proposed mapping before changing it.
