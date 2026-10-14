# Type-upgrade consistency extension v1

This document describes the independent `TUCX` extension batch. It is a child
of the verified `TUC` baseline and must not be mixed with that baseline during
execution or reporting.

## Batch identity

```text
BATCH_ID:        2026-10-13-type-upgrade-consistency-extension-v1
BATCH_KIND:      extension
PARENT_BATCH_ID: 2026-10-13-type-upgrade-consistency
CASE_PREFIX:     TUCX
CASE_COUNT:      13,721
```

The parent baseline is:

```text
BATCH_ID:   2026-10-13-type-upgrade-consistency
CASE_PREFIX: TUC
CASE_COUNT: 8,270
```

## What this batch adds

### GAP-DATA-BEHAVIOR — 4,116 cases

Covers post-DDL behavior rather than metadata only:

- Target-only boundary values.
- INSERT with the target column omitted, exercising constant and expression defaults.
- Collation-equivalent values with different byte representations.
- Intended duplicate conflicts under unique indexes.
- Updates from old-range values to target-only values.
- Delete and reinsert of the same business key.
- Explicit committed transactions.
- Explicit rolled-back transactions.
- Post-DDL data comparisons against directly created reference tables.

### GAP-INDEX-PK — 2,400 cases

Makes the target column itself part of the key organization:

- Single-column target primary key.
- Target as the first member of a composite primary key.
- Target as the middle member of a composite primary key.
- Target as the last member of a composite primary key.
- Primary key plus secondary and unique indexes.
- Multiple overlapping indexes on the target column.
- Full index-definition comparison through `information_schema.statistics`.

### GAP-DDL-MULTI-COLUMN — 1,518 cases

Covers multi-column ALTER statements:

- Two same-family columns.
- Three same-family columns.
- Five mixed-family columns.
- Multiple members of one composite index.
- One safe action mixed with one invalid narrowing action; the ALTER must reject
  atomically and leave the old state intact.

### GAP-FK-ACTION — 3,440 cases

Executes real parent/child behavior after type upgrade:

- Orphan INSERT rejection.
- `ON DELETE CASCADE`.
- `ON DELETE SET NULL`.
- `ON DELETE RESTRICT`.
- `ON DELETE NO ACTION`.
- `ON UPDATE CASCADE`.
- `ON UPDATE SET NULL`.
- `ON UPDATE RESTRICT`.
- `ON UPDATE NO ACTION`.
- Two-level foreign-key propagation.
- Full constraint and referenced-column comparisons.

### GAP-QUERY-ORACLE — 2,247 cases

Adds result and access-path checks:

- Secondary-index scans.
- Unique-index scans.
- Prefix-index scans for long or TEXT/BLOB-like columns.
- Intended unique conflicts.
- Forced-index result equivalence between reference and algorithm tables.
- Ordered full-table/primary-key result comparison.
- EXPLAIN FORMAT=JSON access-path assertions for reference and algorithm tables.
- Prefix-index ordering verification.
- Descending-order verification.

## Artifact directory

```text
mysql_case_factory/generated/type_upgrade_consistency_extension_v1/
```

Important files:

- `cases.jsonl.gz`
- `copy_suite.sql.gz`
- `inplace_suite.sql.gz`
- `instant_suite.sql.gz`
- `manifest.json`
- `coverage.tsv`
- `coverage_gap_report.tsv`
- `coverage_summary.md`
- `README.md`
- `local_results.jsonl`
- `local_summary.json`
- `local_summary.md`

## Local verification

The extension was run fully against isolated local MySQL 8.0.45 using
`ALGORITHM=COPY`:

```text
Selected: 13,721
Executed: 13,721
PASS:     13,721
FAIL:     0
Stopped early: false
MySQL version: 8.0.45
Artifact integrity verified: true
```

The local COPY run is only the local oracle. It is not internal `INPLACE` or
`INSTANT` PASS evidence.

## Coverage audit

Run:

```bash
python3 tools/audit_type_upgrade_extension.py \
  --baseline generated/type_upgrade_consistency \
  --extension generated/type_upgrade_consistency_extension_v1 \
  --report-dir generated/type_upgrade_consistency_extension_v1
```

Current audit result:

```text
Baseline case count: 8,270
Extension case count: 13,721
Case ID overlap: 0
P0 gaps covered: 5/5
COPY/INPLACE/INSTANT profile counts: 13,721 each
Parent link: valid
Forbidden factors: absent
Local COPY: 13,721/13,721 PASS
```

## Internal AI execution rules

1. Verify `manifest.json` before execution.
2. Execute only `TUCX-` cases with the extension batch ID.
3. Do not execute or merge results with `TUC-` baseline cases.
4. Run `INPLACE` and `INSTANT` separately in an isolated internal QA schema.
5. Use `mysql --force` because planned negative cases intentionally return SQL
   errors.
6. The result output must not contain `FAIL`.
7. A server crash, assertion, signal, or MySQL 2013 is `FAIL_CRASH`, never an
   expected negative result.
8. On failure, stop and report batch ID, profile, case ID, gap ID, SQL, error,
   and terminal state.
