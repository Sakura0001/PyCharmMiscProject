# Account, Admin, Maintenance Review Report

Reviewer: account/admin/maintenance sub-agent

Official sources:

- https://dev.mysql.com/doc/refman/8.0/en/account-management-statements.html
- https://dev.mysql.com/doc/refman/8.0/en/alter-user.html
- https://dev.mysql.com/doc/refman/8.0/en/rename-user.html
- https://dev.mysql.com/doc/refman/8.0/en/set-password.html
- https://dev.mysql.com/doc/refman/8.0/en/set-default-role.html
- https://dev.mysql.com/doc/refman/8.0/en/drop-role.html
- https://dev.mysql.com/doc/refman/8.0/en/sql-administration-statements.html
- https://dev.mysql.com/doc/refman/8.0/en/flush.html
- https://dev.mysql.com/doc/refman/8.0/en/kill.html
- https://dev.mysql.com/doc/refman/8.0/en/use.html
- https://dev.mysql.com/doc/refman/8.0/en/help.html
- https://dev.mysql.com/doc/refman/8.0/en/check-table.html
- https://dev.mysql.com/doc/refman/8.0/en/checksum-table.html
- https://dev.mysql.com/doc/refman/8.0/en/optimize-table.html
- https://dev.mysql.com/doc/refman/8.0/en/repair-table.html
- https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-22.html

## Decisions

- Add MySQL account statements missing from the target library:
  `ALTER USER`, `RENAME USER`, `SET PASSWORD`, `SET DEFAULT ROLE`, and
  `DROP ROLE`.
- Do not create `ALTER ROLE`; MySQL 8.0.22 has no independent statement. Map
  PostgreSQL `ALTER ROLE` intent to `ALTER USER`, `SET DEFAULT ROLE`,
  `GRANT`/`REVOKE`, or `DROP ROLE`.
- Add low-risk admin/session statements `FLUSH`, `KILL`, `USE`, and `HELP`.
- Add maintenance statements `CHECK TABLE`, `CHECKSUM TABLE`, `OPTIMIZE TABLE`,
  and `REPAIR TABLE`.
- Add high-risk server statements `SHUTDOWN` and `RESTART` as references whose
  defaults are negative/skipped execution modes.

## Version Exclusions

- Exclude MFA/FIDO clauses from `ALTER USER` because they are 8.0.27+.
- Exclude `REVOKE IF EXISTS` and `IGNORE UNKNOWN USER` because they are 8.0.30+.
- Exclude `ANALYZE TABLE ... USING DATA` because it is 8.0.31+.
- Exclude `explain_format` variable because it is 8.0.32+.
