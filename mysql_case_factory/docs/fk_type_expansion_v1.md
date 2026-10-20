# FK type-expansion consistency batch

## Objective

This batch verifies that expanding a child foreign-key column does not break
parent/child referential integrity under `INPLACE` or `INSTANT`.

The core invariant is:

```text
The DDL result must match the internal algorithm matrix.
Full-table INSERT, UPDATE, and DELETE must not create orphan child rows.
The FK must still exist after DDL.
Parent and child counts must match the selected FK action.
No crash, assertion, MySQL 2013/2006, or lost connection is allowed.
```

## Batch identity

- **BATCH_ID:** `2026-10-20-fk-type-expansion-consistency-v1`
- **BATCH_KIND:** `fk_type_expansion_consistency`
- **CASE_PREFIX:** `TUCFK`
- **Database:** `qa_fk_type_expansion`
- **Cases:** 568
- **Transitions:** 71
- **Profiles:** `inplace`, `instant`
- **FK actions:** `RESTRICT`, `NO ACTION`, `CASCADE`, `SET NULL`
- **Materialization:** compressed SQL suites

## Coverage

| Family | Transitions | Cases |
| --- | ---: | ---: |
| Integer | 22 | 176 |
| Character | 14 | 112 |
| Binary | 12 | 96 |
| Decimal | 10 | 80 |
| Bit | 13 | 104 |
| **Total** | **71** | **568** |

Every transition is executed with both algorithms and all four FK actions.

## Algorithm matrix

| Family | INPLACE | INSTANT |
| --- | --- | --- |
| Integer cross-width | reject, 3780 | reject, 3780 |
| Integer same type | success | success |
| Character expansion | success | reject, 1845 |
| Varbinary expansion | success | reject, 1845 |
| Decimal expansion | success | reject, 1845 |
| Bit expansion | success | reject, 1845 |
| Fixed binary expansion | reject, 1846 | reject, 1846 |

The known `BINARY(10) -> BINARY(20)` orphan case is retained as a mandatory
regression. If the internal build rejects the DDL, the case must prove that no
state changed. If a patch allows it, the case must prove that deleting the
parent cannot leave an orphan child row.

## Scenario design

Each scenario:

1. Creates a parent and child table with a composite foreign key.
2. Seeds 10 deterministic source-boundary rows.
3. Applies one child-column `MODIFY` with `INPLACE` or `INSTANT`.
4. Inserts 10 additional parent and child rows.
5. Updates all parent FK values and child payloads.
6. Exercises the selected FK delete action.
7. Deletes all child rows.
8. Reinserts child rows for surviving parents.
9. Checks:
   - child column type;
   - parent count;
   - child count;
   - orphan count;
   - matched count;
   - FK existence;
   - final `PASS` or `FAIL`.
10. Drops both tables.

## Execution

Create the fixed database:

```bash
mysql --login-path=internal_qa \
  -e "DROP DATABASE IF EXISTS qa_fk_type_expansion; CREATE DATABASE qa_fk_type_expansion CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
```

Run `INPLACE`:

```bash
gunzip -c generated/fk_type_expansion_v1/inplace_suite.sql.gz > /tmp/tucfk-inplace.sql

mysql --login-path=internal_qa \
  --batch --raw --skip-column-names --binary-mode --force \
  qa_fk_type_expansion \
  < /tmp/tucfk-inplace.sql \
  > generated/fk_type_expansion_v1/inplace.actual.tsv \
  2> generated/fk_type_expansion_v1/inplace.errors.log

diff -u generated/fk_type_expansion_v1/expected_output_inplace.tsv \
  generated/fk_type_expansion_v1/inplace.actual.tsv
```

Run `INSTANT`:

```bash
gunzip -c generated/fk_type_expansion_v1/instant_suite.sql.gz > /tmp/tucfk-instant.sql

mysql --login-path=internal_qa \
  --batch --raw --skip-column-names --binary-mode --force \
  qa_fk_type_expansion \
  < /tmp/tucfk-instant.sql \
  > generated/fk_type_expansion_v1/instant.actual.tsv \
  2> generated/fk_type_expansion_v1/instant.errors.log

diff -u generated/fk_type_expansion_v1/expected_output_instant.tsv \
  generated/fk_type_expansion_v1/instant.actual.tsv
```

A run passes only when:

1. stdout matches the expected TSV exactly;
2. every result row ends with `PASS`;
3. orphan count is zero;
4. the FK still exists;
5. no signal, assertion, timeout, MySQL 2013/2006, or lost connection occurs.

## Audit

```bash
PYTHONPATH=src python3 tools/audit_fk_type_expansion.py \
  --fk generated/fk_type_expansion_v1 \
  --skip-local
```

The current audit validates the complete artifact structure, 568 cases, 71
transitions, both profiles, all four FK actions, deterministic hashes, expected
output, SQL oracles, and usage documentation.
