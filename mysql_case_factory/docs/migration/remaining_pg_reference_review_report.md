# Remaining PG Reference Review

Target: MySQL Community Server 8.0.22.

Official sources:
- https://dev.mysql.com/doc/refman/8.0/en/sql-statements.html
- https://dev.mysql.com/doc/refman/8.0/en/sql-transactional-statements.html
- https://dev.mysql.com/doc/refman/8.0/en/set-transaction.html
- https://dev.mysql.com/doc/refman/8.0/en/savepoint.html
- https://dev.mysql.com/doc/refman/8.0/en/sql-prepared-statements.html
- https://dev.mysql.com/doc/refman/8.0/en/grant.html
- https://dev.mysql.com/doc/refman/8.0/en/lock-tables.html
- https://dev.mysql.com/doc/refman/8.0/en/lock-instance-for-backup.html
- https://dev.mysql.com/doc/refman/8.0/en/create-function-loadable.html
- https://dev.mysql.com/doc/refman/8.0/en/drop-function-loadable.html
- https://dev.mysql.com/doc/refman/8.0/en/sql-data-definition-statements.html
- https://dev.mysql.com/doc/refman/8.0/en/create-table.html
- https://dev.mysql.com/doc/refman/8.0/en/create-table-select.html
- https://dev.mysql.com/doc/refman/8.0/en/alter-table.html
- https://dev.mysql.com/doc/refman/8.0/en/analyze-table.html
- https://dev.mysql.com/doc/refman/8.0/en/reset.html
- https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-22.html

## New MySQL References

The review found standalone MySQL 8.0.22 statements that were still missing from the local MySQL factor library:

| Area | Added references |
|---|---|
| Transaction | `SET TRANSACTION` |
| Savepoints | `SAVEPOINT`, `ROLLBACK TO SAVEPOINT`, `RELEASE SAVEPOINT` |
| Locks | `LOCK TABLES`, `UNLOCK TABLES`, `LOCK INSTANCE FOR BACKUP`, `UNLOCK INSTANCE` |
| Dynamic loading | loadable `CREATE FUNCTION`, loadable `DROP FUNCTION` |

Prepared `EXECUTE`, `DEALLOCATE PREPARE`, and `GRANT` were already present; the manifest now records their PG source coverage.

## Merge Decisions

Several PostgreSQL statements are valid migration intents but not MySQL standalone statement names:

| PG area | MySQL 8.0.22 landing point |
|---|---|
| `ABORT`, transaction `END` | `ROLLBACK` and `COMMIT` |
| `VACUUM` | `OPTIMIZE TABLE` and `ANALYZE TABLE` |
| `LOAD` | plugin/component and loadable-function administration |
| `COMMENT ON` | inline comments on table, column, index, routine, event, and account statements |
| `CREATE DOMAIN`, `CREATE TYPE`, `CREATE SEQUENCE`, collations | inline table/routine/database factors such as column types, `CHECK`, `AUTO_INCREMENT`, charset, and collation |
| materialized views | table plus event/procedure refresh patterns |
| foreign tables | `ENGINE=FEDERATED`, `CONNECTION`, and `CREATE SERVER` coverage |
| `CREATE TABLE AS`, table-creating `SELECT INTO` | `CREATE TABLE ... SELECT` |
| PostgreSQL extended statistics | `ANALYZE TABLE` histogram coverage |

## PG-Only Decisions

The remaining DDL-only PostgreSQL object families are marked `drop_pg_only` in the manifest because MySQL 8.0.22 has no matching SQL object model: access methods, aggregates, casts, conversions, languages, operators, operator classes/families, rules, policies, publications, subscriptions, ownership reassignment, default privileges, security labels, large objects, FDW/user-mapping/import-foreign-schema objects, text search objects, and transforms.

## Version Exclusions

The following current-manual features are explicitly excluded from the 8.0.22 target:

- `CREATE FUNCTION/PROCEDURE/TRIGGER IF NOT EXISTS`: 8.0.29+.
- loadable `CREATE FUNCTION ... IF NOT EXISTS`: 8.0.29+.
- invisible columns and `AUTOEXTEND_SIZE`: 8.0.23+.
- generated invisible primary keys: 8.0.30+.
- `ANALYZE TABLE ... UPDATE HISTOGRAM ... USING DATA`: 8.0.31+.
- `INSTALL COMPONENT ... SET`: 8.0.33+.
- `ALTER INSTANCE RELOAD KEYRING`: 8.0.24+.
