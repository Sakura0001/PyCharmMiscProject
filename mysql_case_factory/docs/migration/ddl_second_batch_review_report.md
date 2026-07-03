# DDL Second Batch Review Report

Reviewer: DDL second-batch sub-agent

This report covers database/schema/view/table/drop-index statements reviewed
against MySQL Community Server 8.0.22 official documentation.

Official sources:

- https://dev.mysql.com/doc/refman/8.0/en/sql-statements.html
- https://dev.mysql.com/doc/refman/8.0/en/alter-database.html
- https://dev.mysql.com/doc/refman/8.0/en/drop-database.html
- https://dev.mysql.com/doc/refman/8.0/en/create-view.html
- https://dev.mysql.com/doc/refman/8.0/en/alter-view.html
- https://dev.mysql.com/doc/refman/8.0/en/drop-view.html
- https://dev.mysql.com/doc/refman/8.0/en/alter-table.html
- https://dev.mysql.com/doc/refman/8.0/en/drop-table.html
- https://dev.mysql.com/doc/refman/8.0/en/truncate-table.html
- https://dev.mysql.com/doc/refman/8.0/en/drop-index.html
- https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-22.html
- https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-23.html

## Decisions

- `ALTER DATABASE`: `rewrite_for_mysql`. Keep only database default character
  set, collation, encryption, and `READ ONLY`; drop PostgreSQL owner,
  connection limit, tablespace, collation refresh, and parameter set/reset
  factors. `READ ONLY` is included because MySQL 8.0.22 introduced it.
- `DROP DATABASE`: `rewrite_for_mysql`. Keep `IF EXISTS` and object state;
  drop PostgreSQL `WITH (FORCE)` and active-connection factors.
- `CREATE/ALTER/DROP SCHEMA`: `rewrite_for_mysql` as database synonyms.
- `CREATE VIEW`: `rewrite_for_mysql`. Keep `OR REPLACE`, column list, and
  check option; add `ALGORITHM`, `DEFINER`, and `SQL SECURITY`; drop
  PostgreSQL temporary/recursive view and view option factors.
- `ALTER VIEW`: `rewrite_for_mysql` as MySQL view redefinition.
- `DROP VIEW`: `rewrite_for_mysql`; `RESTRICT` and `CASCADE` are parsed but
  ignored by MySQL.
- `ALTER TABLE`: `rewrite_for_mysql`, pending a full reference file. Add MySQL
  `ALGORITHM`, `LOCK`, column/index/constraint/table-option/partition
  operations. Exclude invisible columns and `AUTOEXTEND_SIZE` because they are
  8.0.23+.
- `DROP TABLE`: `rewrite_for_mysql`. Add `TEMPORARY`; treat `RESTRICT` and
  `CASCADE` as parsed no-ops.
- `TRUNCATE TABLE`: `rewrite_for_mysql`; MySQL has one table target, resets
  auto-increment, implicitly commits, and fails when referenced by foreign keys.
- `DROP INDEX`: `rewrite_for_mysql`; require `ON tbl_name` and add
  `ALGORITHM`/`LOCK`. Drop PostgreSQL `CONCURRENTLY`, `IF EXISTS`, multi-index,
  and dependency cascade factors.
