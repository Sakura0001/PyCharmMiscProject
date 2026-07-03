# Cursor, XA, Data Transfer Review Report

Reviewer: cursor/XA/data-transfer sub-agent

Official sources:

- https://dev.mysql.com/doc/refman/8.0/en/cursors.html
- https://dev.mysql.com/doc/refman/8.0/en/declare-cursor.html
- https://dev.mysql.com/doc/refman/8.0/en/open.html
- https://dev.mysql.com/doc/refman/8.0/en/fetch.html
- https://dev.mysql.com/doc/refman/8.0/en/close.html
- https://dev.mysql.com/doc/refman/8.0/en/xa-statements.html
- https://dev.mysql.com/doc/refman/8.0/en/load-data.html
- https://dev.mysql.com/doc/refman/8.0/en/load-xml.html
- https://dev.mysql.com/doc/refman/8.0/en/replace.html
- https://dev.mysql.com/doc/refman/8.0/en/do.html
- https://dev.mysql.com/doc/refman/8.0/en/handler.html
- https://dev.mysql.com/doc/refman/8.0/en/import-table.html
- https://dev.mysql.com/doc/refman/8.0/en/select-into.html

## Decisions

- Rewrite PostgreSQL cursor statements into MySQL stored-program cursor
  lifecycle: `DECLARE`, `OPEN`, `FETCH`, `CLOSE`.
- Drop PostgreSQL `MOVE` cursor; MySQL cursors are nonscrollable, read-only,
  and asensitive.
- Rewrite PostgreSQL two-phase transaction statements into MySQL XA family:
  `XA START/BEGIN`, `XA END`, `XA PREPARE`, `XA COMMIT`, `XA ROLLBACK`, and
  `XA RECOVER`.
- Add MySQL `DO`, `REPLACE`, `LOAD DATA`, `LOAD XML`, `HANDLER`, and
  `IMPORT TABLE` references.
- Extend `SELECT` with `INTO` destination factor for variables, `OUTFILE`, and
  `DUMPFILE`.

## Version Notes

The MySQL 8.0.22 factor set should not include XA behavior documented only for
later replication-filter changes.
