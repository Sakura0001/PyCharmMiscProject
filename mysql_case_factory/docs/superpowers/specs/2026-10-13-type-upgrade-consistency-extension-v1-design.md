# Type-upgrade consistency extension v1 design

## Background

The existing `2026-10-13-type-upgrade-consistency` batch contains 8,270 `TUC`
cases and is a complete, locally verified baseline. It intentionally uses a
clustered expansion strategy: every retained type transition receives baseline,
attribute, and compatible-index coverage, while foreign keys, dependency
objects, table forms, and SQL modes use representative anchors.

The next batch must not overwrite or mutate the verified baseline. It will be
an independent extension batch that closes high-risk interaction gaps.

## Batch identity

```text
BATCH_ID:       2026-10-13-type-upgrade-consistency-extension-v1
BATCH_KIND:     extension
PARENT_BATCH_ID: 2026-10-13-type-upgrade-consistency
CASE_PREFIX:    TUCX
```

Artifacts will be written to:

```text
mysql_case_factory/generated/type_upgrade_consistency_extension_v1/
```

The baseline artifacts in
`mysql_case_factory/generated/type_upgrade_consistency/` must remain byte-for-byte
unchanged.

## Scope retained from the baseline

- Integer, DECIMAL/NUMERIC, character, binary, and BIT type upgrades.
- SQL-direct execution only.
- Local MySQL 8.0.45 `COPY` verification.
- Internal `INPLACE` and `INSTANT` suites with the same case IDs.
- Result correctness, data correctness, schema correctness, index correctness,
  foreign-key correctness, and dependency-object correctness.

## Factors still excluded

- FLOAT, DOUBLE, and REAL.
- DATE, TIME, DATETIME, TIMESTAMP, and YEAR.
- ENUM and SET.
- JSON, spatial, and vector types.
- FULLTEXT, SPATIAL, and JSON multi-value indexes.
- Temporal SQL modes and `time_zone`.
- Backup/PITR, crash injection, resource faults, HA switchover, control-plane
  APIs, connection loss, cancellation, retry, and concurrent DDL/DML.

## P0 gaps to close

### GAP-DATA-BEHAVIOR

Add post-DDL behavior profiles:

- `post_target_boundary`: target-only boundary values.
- `default_omission`: INSERT omits the target column and exercises its default.
- `collation_equivalent`: values equal under collation but different by bytes.
- `duplicate_conflict`: intended unique conflicts.
- `update_old_to_new`: old values become target-only values.
- `delete_reinsert`: delete and reinsert the same business key.
- `commit_ledger`: explicit committed transaction.
- `rollback_ledger`: explicit rolled-back transaction.

### GAP-INDEX-PK

Make the target column a primary key and cover:

- Single-column target primary key.
- Target as first, middle, and last member of a composite primary key.
- Primary key plus secondary and unique indexes.
- Multiple overlapping indexes on the target column.

### GAP-DDL-MULTI-COLUMN

Cover one ALTER that modifies:

- Two columns of the same family.
- Three columns of the same family.
- Five columns across retained families.
- Multiple members of one composite index.
- A safe action mixed with an invalid action; the statement must reject
  atomically.

### GAP-FK-ACTION

For real reference/algorithm table pairs, execute and verify:

- Orphan INSERT rejection.
- `ON DELETE CASCADE`.
- `ON DELETE SET NULL`.
- `ON DELETE RESTRICT` / `NO ACTION`.
- `ON UPDATE CASCADE`.
- `ON UPDATE SET NULL`.
- `ON UPDATE RESTICT` / `NO ACTION`.
- Propagation through a two-level foreign-key chain.

### GAP-QUERY-ORACLE

Compare more than metadata:

- Full-table/primary-key ordered result.
- `FORCE INDEX` result.
- `EXPLAIN FORMAT=JSON` access-path evidence for reference and algorithm tables.
- Unique-conflict behavior.
- Descending and prefix-index ordering.

## P1 follow-up gaps

P1 is planned but not required for extension v1 completion:

- Charset/collation conversion matrix.
- Richer views, triggers, functions, procedures, and prepared statements.
- Mixed ALTER actions and consecutive ALTER histories.
- Target-column partition-key behavior.
- Extended boundary matrices for BIT, character, binary, and DECIMAL.
- Exact errno/SQLSTATE/warning contracts for every negative case.

## Case model

Each extension case adds:

```json
{
  "batch_id": "2026-10-13-type-upgrade-consistency-extension-v1",
  "batch_kind": "extension",
  "parent_batch_id": "2026-10-13-type-upgrade-consistency",
  "case_id": "TUCX-000001",
  "priority": "P0",
  "gap_id": "GAP-INDEX-PK",
  "coverage_tags": ["INDEX", "PRIMARY_KEY"],
  "interaction_rank": 2
}
```

The runner and suites continue to use the four-table model:

- `T_old`
- `T_ref`
- `T_algo`
- auxiliary FK, trigger, audit, and snapshot tables as needed.

## Determinism and evidence

- Generation is deterministic.
- Manifest records artifact SHA-256 and byte size.
- Local COPY must execute every generated extension case, not a sample.
- Any server crash, assertion, signal, or MySQL 2013 is `FAIL_CRASH`.
- Planned negative DDL errors may occur, but verification output must not
  contain `FAIL`.
- Internal PASS is valid only for internal `INPLACE` or `INSTANT`; local COPY
  is only the local oracle.

## Acceptance criteria for extension v1

1. Baseline `TUC` artifacts remain unchanged.
2. Every extension case uses `TUCX-` and the extension batch identity.
3. Every P0 gap has at least one passing case.
4. Generated case count is driven by coverage, not padding.
5. Full local COPY run passes every extension case.
6. `pytest -q` passes.
7. `COPY`, `INPLACE`, and `INSTANT` suites have identical case ID sequences.
8. Coverage audit reports zero P0 gaps and zero forbidden factors.
9. Documentation and internal-AI README distinguish `TUC` and `TUCX`.
