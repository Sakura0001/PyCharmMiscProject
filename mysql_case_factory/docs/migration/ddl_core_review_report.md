# DDL Core Factor Review Report

Reviewer: DDL core sub-agent

Scope:

- `ddl/table/*.md`
- `ddl/index/*.md`
- `ddl/database/*.md`
- `ddl/schema/*.md`
- `ddl/view/*.md`

Official sources:

- https://dev.mysql.com/doc/refman/8.0/en/sql-statements.html
- https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-22.html
- https://dev.mysql.com/doc/refman/8.0/en/create-table.html
- https://dev.mysql.com/doc/refman/8.0/en/alter-table.html
- https://dev.mysql.com/doc/refman/8.0/en/drop-table.html
- https://dev.mysql.com/doc/refman/8.0/en/create-index.html
- https://dev.mysql.com/doc/refman/8.0/en/drop-index.html
- https://dev.mysql.com/doc/refman/8.0/en/create-database.html
- https://dev.mysql.com/doc/refman/8.0/en/create-view.html

## Decisions

- `CREATE TABLE`: `rewrite_for_mysql`. Keep table creation, rewrite to MySQL
  column definitions, `CREATE TABLE ... SELECT`, and `CREATE TABLE ... LIKE`.
  Drop PostgreSQL `UNLOGGED`, `INHERITS`, typed table, storage, compression,
  and OID factors.
- `ALTER TABLE`: `rewrite_for_mysql`. Keep add/drop/modify/change columns,
  constraints, indexes, rename, partition operations; add MySQL `ALGORITHM`,
  `LOCK`, and table options.
- `DROP TABLE`: `rewrite_for_mysql`. Keep `IF EXISTS` and multi-table drop;
  add `TEMPORARY`. MySQL parses and ignores `RESTRICT` and `CASCADE`.
- `CREATE INDEX`: `rewrite_for_mysql`. Keep index creation but replace
  PostgreSQL access methods with MySQL `UNIQUE`, `FULLTEXT`, `SPATIAL`,
  `USING BTREE/HASH`, key part length, visibility, parser, comment, algorithm,
  and lock options.
- `ALTER INDEX`: `rewrite_for_mysql` only through `ALTER TABLE ... RENAME
  INDEX` and `ALTER TABLE ... ALTER INDEX ... VISIBLE|INVISIBLE`.
- `REINDEX`, `CLUSTER`, and PostgreSQL `SELECT INTO` table creation:
  `drop_pg_only`.
- `CREATE/ALTER/DROP DATABASE` and `CREATE/ALTER/DROP SCHEMA`:
  `rewrite_for_mysql`; MySQL `SCHEMA` is a database synonym.
- `CREATE/ALTER/DROP VIEW`: `rewrite_for_mysql`; add MySQL `ALGORITHM`,
  `DEFINER`, and `SQL SECURITY`.

## Version Exclusions

- Invisible columns are MySQL 8.0.23+, not 8.0.22.
- Generated invisible primary keys are MySQL 8.0.30+, not 8.0.22.
