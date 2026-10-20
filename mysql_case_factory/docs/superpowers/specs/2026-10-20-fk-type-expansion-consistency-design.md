# FK type-expansion consistency design

## Goal

Verify that expanding a child foreign-key column with `ALTER TABLE ... MODIFY`
does not break parent/child referential integrity under `INPLACE` or `INSTANT`.
The suite must detect the known orphan-row defect shown by:

```sql
CREATE TABLE s1p (id INT PRIMARY KEY, b BINARY(10), KEY(b)) ENGINE=InnoDB;
CREATE TABLE s1c (id INT PRIMARY KEY, b BINARY(10),
  CONSTRAINT fk FOREIGN KEY (b) REFERENCES s1p(b)) ENGINE=InnoDB;
INSERT INTO s1p VALUES (1,'aaa');
INSERT INTO s1c VALUES (1,'aaa');
ALTER TABLE s1c MODIFY b BINARY(20), ALGORITHM=INPLACE;
DELETE FROM s1p WHERE id=1; -- must not leave an orphan in s1c
```

## Scope

- Child-side FK column expansion only.
- Algorithms: `INPLACE`, `INSTANT`.
- FK actions: `RESTRICT`, `NO ACTION`, `CASCADE`, `SET NULL`.
- Type families and minimum transition counts:
  - Integer: 20 transitions, signed and unsigned.
  - Character: 14 transitions.
  - Binary: 12 transitions.
  - Decimal: 10 transitions.
  - Bit: 13 transitions.
- Total: 71 transitions × 2 algorithms × 4 FK actions = 568 scenarios.
- Every scenario uses a parent table and a child table.
- Every scenario performs full-table `INSERT`, `UPDATE`, and `DELETE` after DDL.
- Every scenario checks:
  - final parent row count;
  - final child row count;
  - orphan child count;
  - matched parent/child count;
  - FK definition still exists;
  - no crash, assertion, MySQL 2013/2006, or lost connection.

## Type transition matrix

### Integer

Signed and unsigned variants of:

1. `TINYINT -> SMALLINT`
2. `TINYINT -> MEDIUMINT`
3. `TINYINT -> INT`
4. `TINYINT -> BIGINT`
5. `SMALLINT -> MEDIUMINT`
6. `SMALLINT -> INT`
7. `SMALLINT -> BIGINT`
8. `MEDIUMINT -> INT`
9. `MEDIUMINT -> BIGINT`
10. `INT -> BIGINT`
11. `BIGINT -> BIGINT`

### Character

1. `CHAR(0) -> CHAR(1)`
2. `CHAR(1) -> CHAR(2)`
3. `CHAR(10) -> CHAR(20)`
4. `CHAR(50) -> CHAR(100)`
5. `CHAR(100) -> CHAR(200)`
6. `CHAR(255) -> VARCHAR(256)`
7. `VARCHAR(0) -> VARCHAR(1)`
8. `VARCHAR(1) -> VARCHAR(2)`
9. `VARCHAR(10) -> VARCHAR(20)`
10. `VARCHAR(60) -> VARCHAR(100)`
11. `VARCHAR(100) -> VARCHAR(200)`
12. `VARCHAR(255) -> VARCHAR(256)`
13. `VARCHAR(512) -> VARCHAR(1024)`
14. `VARCHAR(2048) -> VARCHAR(4096)`

### Binary

1. `BINARY(0) -> BINARY(1)`
2. `BINARY(1) -> BINARY(2)`
3. `BINARY(10) -> BINARY(20)`
4. `BINARY(50) -> BINARY(100)`
5. `BINARY(100) -> BINARY(200)`
6. `BINARY(255) -> VARBINARY(256)`
7. `VARBINARY(0) -> VARBINARY(1)`
8. `VARBINARY(1) -> VARBINARY(2)`
9. `VARBINARY(10) -> VARBINARY(20)`
10. `VARBINARY(60) -> VARBINARY(100)`
11. `VARBINARY(255) -> VARBINARY(256)`
12. `VARBINARY(512) -> VARBINARY(1024)`

### Decimal

1. `DECIMAL(1,0) -> DECIMAL(2,0)`
2. `DECIMAL(5,2) -> DECIMAL(10,2)`
3. `DECIMAL(10,2) -> DECIMAL(18,2)`
4. `DECIMAL(18,6) -> DECIMAL(28,6)`
5. `DECIMAL(28,10) -> DECIMAL(38,10)`
6. `DECIMAL(38,18) -> DECIMAL(50,18)`
7. `DECIMAL(50,30) -> DECIMAL(65,30)`
8. `DECIMAL(65,30) -> DECIMAL(65,30)`
9. `DECIMAL(10,0) -> DECIMAL(20,0)`
10. `DECIMAL(20,4) -> DECIMAL(30,4)`

### Bit

1. `BIT(0) -> BIT(1)`
2. `BIT(1) -> BIT(2)`
3. `BIT(2) -> BIT(4)`
4. `BIT(4) -> BIT(8)`
5. `BIT(8) -> BIT(16)`
6. `BIT(16) -> BIT(24)`
7. `BIT(24) -> BIT(32)`
8. `BIT(32) -> BIT(40)`
9. `BIT(40) -> BIT(48)`
10. `BIT(48) -> BIT(56)`
11. `BIT(56) -> BIT(64)`
12. `BIT(63) -> BIT(64)`
13. `BIT(64) -> BIT(64)`

## Expected algorithm behavior

| Family | INPLACE | INSTANT |
| --- | --- | --- |
| Integer cross-width | reject, 3780 | reject, 3780 |
| Integer same type | success | success |
| Character expansion | success | reject, 1845 |
| Varbinary expansion | success | reject, 1845 |
| Decimal expansion | success | reject, 1845 |
| Bit expansion | success | reject, 1845 |
| Fixed binary expansion | reject, 1846 | reject, 1846 |

The known `BINARY(10) -> BINARY(20)` orphan case is intentionally retained as a
mandatory regression. If the internal build rejects it, the case must assert
rejection and no state change. If a patch allows it, the case must prove that
deleting the parent cannot leave an orphan child row.

## Data and DML design

Each scenario seeds 10 deterministic boundary rows in the source type. After
DDL, it performs:

1. Insert 10 additional parent rows and 10 child rows.
2. Update all parent FK values to a second deterministic value set.
3. Update all child non-FK payload values.
4. Exercise the selected FK delete action.
5. Delete all child rows.
6. Reinsert child rows for the remaining parents.
7. Query parent count, child count, orphan count, and matched count.
8. Query `information_schema.KEY_COLUMN_USAGE` to prove the FK still exists.

All DML is full-table or full-selected-set DML, not single-row-only smoke.

## Deliverables

- `src/mysql_case_factory/fk_type_expansion.py`
- `tools/generate_fk_type_expansion.py`
- `tools/audit_fk_type_expansion.py`
- `tests/test_fk_type_expansion.py`
- `tests/test_fk_type_expansion_audit.py`
- `generated/fk_type_expansion_v1/`
- `docs/fk_type_expansion_v1.md`
