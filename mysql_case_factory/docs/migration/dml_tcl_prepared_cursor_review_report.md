# DML, TCL, Prepared, Cursor Factor Review Report

Reviewer: DML/TCL/prepared/cursor sub-agent

Official sources:

- https://dev.mysql.com/doc/refman/8.0/en/sql-statements.html
- https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-22.html
- https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-19.html
- https://dev.mysql.com/doc/refman/8.0/en/insert.html
- https://dev.mysql.com/doc/refman/8.0/en/update.html
- https://dev.mysql.com/doc/refman/8.0/en/delete.html
- https://dev.mysql.com/doc/refman/8.0/en/commit.html
- https://dev.mysql.com/doc/refman/8.0/en/savepoint.html
- https://dev.mysql.com/doc/refman/8.0/en/sql-prepared-statements.html
- https://dev.mysql.com/doc/refman/8.0/en/cursors.html

## Decisions

- `SELECT`, `VALUES`, `CALL`, `INSERT`, `UPDATE`, and `DELETE`:
  `rewrite_for_mysql`.
- `MERGE`: `drop_pg_only`; MySQL 8.0.22 has no `MERGE` statement.
- `BEGIN` / `START TRANSACTION`, `COMMIT`, `ROLLBACK`, `SET TRANSACTION`,
  `SAVEPOINT`, `ROLLBACK TO SAVEPOINT`, `RELEASE SAVEPOINT`:
  `rewrite_for_mysql`.
- `ABORT` and transaction `END`: `drop_pg_only`.
- PostgreSQL two-phase transaction statements: `drop_pg_only`; add MySQL XA
  statement family instead.
- `PREPARE`, `EXECUTE`, `DEALLOCATE`: `rewrite_for_mysql` with MySQL session
  prepared statement semantics.
- Cursor statements: rewrite to stored-program cursor lifecycle and add `OPEN`;
  drop PostgreSQL `MOVE`.

## MySQL Missing Coverage

Add DML statements and factors for `DO`, `HANDLER`, `IMPORT TABLE`, `LOAD DATA`,
`LOAD XML`, `REPLACE`, `TABLE`, `UNION`, `SELECT ... INTO`, and XA transaction
statements. `TABLE` and `VALUES` are available in 8.0.22 because they were
introduced in 8.0.19. `INTERSECT` and `EXCEPT` are 8.0.31+ and must be
excluded.
