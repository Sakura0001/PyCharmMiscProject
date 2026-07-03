# DML Query/Table Review Report

Reviewer: DML query/table sub-agent

Official sources:

- https://dev.mysql.com/doc/refman/8.0/en/select.html
- https://dev.mysql.com/doc/refman/8.0/en/update.html
- https://dev.mysql.com/doc/refman/8.0/en/delete.html
- https://dev.mysql.com/doc/refman/8.0/en/values.html
- https://dev.mysql.com/doc/refman/8.0/en/call.html
- https://dev.mysql.com/doc/refman/8.0/en/with.html
- https://dev.mysql.com/doc/refman/8.0/en/table.html
- https://dev.mysql.com/doc/refman/8.0/en/union.html
- https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-19.html
- https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-31.html

## Decisions

- `SELECT`: `rewrite_for_mysql`. Keep query semantics, `WITH`, `UNION`,
  window, `LIMIT`, locking reads, and `SELECT ... INTO`. Exclude
  `INTERSECT`/`EXCEPT` because they are 8.0.31+.
- `VALUES`: `rewrite_for_mysql` as `VALUES ROW(...) ...`; introduced in 8.0.19
  and therefore available in 8.0.22.
- `UPDATE`: `rewrite_for_mysql` as MySQL single-table and multiple-table
  variants. Single-table supports `ORDER BY` and `LIMIT`; multiple-table does
  not.
- `DELETE`: `rewrite_for_mysql` as MySQL single-table and multiple-table
  variants.
- `MERGE`: `drop_pg_only`; MySQL 8.0.22 has no SQL `MERGE INTO` statement.
- `CALL`: `rewrite_for_mysql` for stored procedures, including OUT/INOUT user
  variables and no-argument calls with optional parentheses.

## Required MySQL Additions

Add `TABLE` statement coverage and later extend `INSERT` with an
`INSERT ... TABLE` branch. Do not add PG `MERGE` as a statement reference.
