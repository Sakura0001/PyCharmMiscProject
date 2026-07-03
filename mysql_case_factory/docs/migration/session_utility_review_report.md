# Session, Utility, DCL Factor Review Report

Reviewer: DCL/session/utility sub-agent

Official sources:

- https://dev.mysql.com/doc/refman/8.0/en/account-management-statements.html
- https://dev.mysql.com/doc/refman/8.0/en/create-user.html
- https://dev.mysql.com/doc/refman/8.0/en/grant.html
- https://dev.mysql.com/doc/refman/8.0/en/revoke.html
- https://dev.mysql.com/doc/refman/8.0/en/set-role.html
- https://dev.mysql.com/doc/refman/8.0/en/set-variable.html
- https://dev.mysql.com/doc/refman/8.0/en/show.html
- https://dev.mysql.com/doc/refman/8.0/en/reset.html
- https://dev.mysql.com/doc/refman/8.0/en/explain.html
- https://dev.mysql.com/doc/refman/8.0/en/analyze-table.html
- https://dev.mysql.com/doc/refman/8.0/en/load-data.html

## Decisions

- `GRANT`, `REVOKE`, `SET ROLE`, `SET`, `SHOW`, `RESET`, `EXPLAIN`,
  `ANALYZE`, `LOCK`, `DO`, `LOAD`, and `COPY`: `rewrite_for_mysql`.
- `SET SESSION AUTHORIZATION`, `SET CONSTRAINTS`, `LISTEN`, `NOTIFY`,
  `UNLISTEN`, `DISCARD`, `VACUUM`, and `CHECKPOINT`: `drop_pg_only`.
- PostgreSQL anonymous `DO` is not retained; MySQL `DO expr` is a DML-style
  expression execution statement.
- PostgreSQL `COPY` maps to MySQL `LOAD DATA`, `LOAD XML`, and
  `SELECT ... INTO OUTFILE`.

## MySQL Missing Coverage

Add account management statements (`CREATE USER`, `ALTER USER`, `DROP USER`,
`RENAME USER`, `CREATE ROLE`, `DROP ROLE`, `SET DEFAULT ROLE`, `SET PASSWORD`),
SHOW statement families, table maintenance (`CHECK TABLE`, `CHECKSUM TABLE`,
`OPTIMIZE TABLE`, `REPAIR TABLE`), locking/admin (`LOCK TABLES`,
`LOCK INSTANCE FOR BACKUP`, `FLUSH`), and plugin/component/loadable function
statements.

Exclude later syntax from the 8.0.22 library: MFA/FIDO clauses are 8.0.27+,
`REVOKE IF EXISTS` and `IGNORE UNKNOWN USER` are 8.0.30+, `ANALYZE TABLE ...
USING DATA` is 8.0.31+, and the `explain_format` variable is 8.0.32+.
