# Type-upgrade boundary extension v1

This batch closes the boundary gaps discovered after the internal
`BINARY(0) -> BINARY(1)` corruption case. It is independent from `TUC`, `TUCX`,
`TUCS`, and `TUCP`.

## Identity

- **BATCH_ID:** `2026-10-15-type-upgrade-boundary-v1`
- **BATCH_KIND:** `boundary_extension`
- **PARENT_BATCH_ID:** `2026-10-15-type-upgrade-pipeline-v1`
- **CASE_PREFIX:** `TUCZ`
- **CASE_COUNT:** 750
- **Profiles:** `COPY`, `INPLACE`, `INSTANT`
- **SQL files:** 2,250
- **Fixed QA database:** `qa_type_upgrade_boundary`

## Core oracle

Every case uses a reference table and an algorithm table. The reference table is
created directly in the final target shape. The algorithm table starts in the
source shape and executes two upgrades:

1. Insert 24 deterministic source rows.
2. Upgrade source type to intermediate type.
3. Insert 24 intermediate target-boundary rows.
4. Upgrade intermediate type to final target type.
5. Insert 24 final target-boundary rows.
6. Compare every row and every column against the reference table.

This directly addresses both required data phases:

- rows that existed before the first upgrade;
- rows written after an upgrade and then read through another upgrade.

The assertions also compare:

- column metadata and ordinal position;
- all row data;
- index metadata;
- selected foreign-key constraints;
- selected persistent table statistics.

## Category counts

| Category | Cases |
| --- | ---: |
| `zero_core` | 512 |
| `zero_cross` | 112 |
| `decimal_max` | 64 |
| `variable_max` | 20 |
| `variable_overflow` | 10 |
| `alias_normalization` | 32 |
| **Total** | **750** |

## Zero-length boundary

Covered source types:

- `CHAR(0)`
- `VARCHAR(0)`
- `BINARY(0)`
- `VARBINARY(0)`
- `NCHAR(0)`
- `NVARCHAR(0)`
- `CHARACTER(0)`
- `CHARACTER VARYING(0)`

Covered chains include:

- fixed to fixed;
- fixed to variable;
- variable to fixed;
- variable to variable;
- character to binary;
- binary to character;
- character to `TEXT`;
- binary to `BLOB`.

The key semantic differences are asserted explicitly:

- `BINARY(0) -> BINARY(1)` expects `x'00'`;
- `BINARY(0) -> VARBINARY(1)` expects `x''`;
- `CHAR(0) -> CHAR(1)` expects `''`;
- `CHAR(0) -> BINARY(1)` expects `x'00'`;
- `BINARY(0) -> CHAR(1)` expects `''`.

Zero-length source columns cannot be indexed directly. Selected cases therefore
add an index in the same first ALTER after the column becomes non-zero length.

## Decimal maximum boundary

Covered chains:

```text
DECIMAL(63,30)  -> DECIMAL(64,30)  -> DECIMAL(65,30)
NUMERIC(63,30)  -> NUMERIC(64,30)  -> NUMERIC(65,30)
DECIMAL(63,30)  -> NUMERIC(64,30)  -> NUMERIC(65,30)
NUMERIC(63,30)  -> DECIMAL(64,30)  -> DECIMAL(65,30)
```

The batch reaches MySQL's maximum precision 65 and maximum scale 30 through a
positive two-stage upgrade, rather than only downgrading from `DECIMAL(65,30)`.

## Variable row-size boundary

The fixed fixture shape uses:

```text
id BIGINT primary key
v target variable column
c VARCHAR(50)
d CHAR(20)
e INT
f BIGINT
```

For this exact shape on local MySQL 8.0.45, the maximum lengths are:

| Column | Maximum |
| --- | ---: |
| `VARCHAR` utf8mb4 | 16307 |
| `VARCHAR` utf8mb3 | 21743 |
| `VARCHAR` latin1 | 65231 |
| `VARCHAR` ascii | 65231 |
| `VARBINARY` | 65231 |

Cases cover:

```text
max-2 -> max-1 -> max
```

Overflow cases cover:

```text
VARCHAR(max-1)  -> TEXT
VARBINARY(max-1) -> BLOB
```

These values are fixture-specific, not universal server constants.

## Alias and normalization boundary

Covered source syntax includes:

- `BOOL`
- `BOOLEAN`
- `TINYINT(1)`
- `INT(0)`
- `INT UNSIGNED ZEROFILL`
- `DEC`
- `FIXED`
- bare `DECIMAL`
- bare `NUMERIC`
- bare `BIT`
- bare `BINARY`
- bare `CHAR`
- `NCHAR(0)`
- `NVARCHAR(0)`
- `CHARACTER(0)`
- `CHARACTER VARYING(0)`

These cases verify both data preservation and normalized schema metadata.

## Attribute, position, row-format, and engine interactions

Attribute transitions:

- `NOT NULL DEFAULT ... -> NULL`
- `NOT NULL DEFAULT ... -> NOT NULL DEFAULT ...`
- `NOT NULL` without default
- nullable

Column positions:

- no position clause;
- no-op `AFTER id`;
- actual `AFTER c`;
- `FIRST`.

InnoDB row formats:

- `DYNAMIC`
- `COMPACT`
- `COMPRESSED`
- `REDUNDANT`

Selected cases also include a stable foreign-key carrier and persistent
statistics checks.

## Artifacts

All artifacts are under:

```text
generated/type_upgrade_boundary_v1
```

Important files:

- `manifest.json`
- `cases.jsonl.gz`
- `coverage.tsv`
- `expected_output.tsv`
- `expected/TUCZ-000001.tsv` through `expected/TUCZ-000750.tsv`
- `copy/TUCZ-000001.sql` through `copy/TUCZ-000750.sql`
- `inplace/TUCZ-000001.sql` through `inplace/TUCZ-000750.sql`
- `instant/TUCZ-000001.sql` through `instant/TUCZ-000750.sql`
- `local_results.jsonl`
- `local_summary.json`
- `local_summary.md`
- `audit_report.json`
- `audit_summary.md`

## Local verification

```text
Selected: 750
Executed: 750
PASS:     752 (750 scenarios + COMBINED_OUTPUT + FINAL_CLEANUP)
FAIL:     0
MySQL:    8.0.45
```

The local runner executes every COPY SQL file separately, executes all files as
one concatenated SQL stream, compares exact stdout, requires empty stderr, and
checks that no `tab_tucz_*` tables or routines remain.

## Independent audit

```text
Profile counts: copy=750, inplace=750, instant=750
Parent overlap: 0
Unique tables: 1,520
SQL line range: 174-186
Two-stage with intermediate insert: true
Semantic checks: 14/14
Local COPY: all PASS
```

## Internal execution

See
[generated/type_upgrade_boundary_v1/README.md](../generated/type_upgrade_boundary_v1/README.md)
for exact commands. In summary:

1. Create or recreate `qa_type_upgrade_boundary`.
2. Run `copy/*.sql`, `inplace/*.sql`, and `instant/*.sql` separately.
3. Compare each profile's stdout with `expected_output.tsv`.
4. Require empty stderr.
5. Do not rewrite expected output.
6. Report batch ID, profile, nearest case ID, SQL, stderr, terminal state, and
   output diff for every failure.
