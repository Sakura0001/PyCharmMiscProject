# Remaining DDL Domain Review Report

Reviewer: remaining-DDL sub-agent

Official sources:

- https://dev.mysql.com/doc/refman/8.0/en/sql-statements.html
- https://dev.mysql.com/doc/refman/8.0/en/sql-data-definition-statements.html
- https://dev.mysql.com/doc/refman/8.0/en/stored-objects.html
- https://dev.mysql.com/doc/refman/8.0/en/create-procedure.html
- https://dev.mysql.com/doc/refman/8.0/en/create-trigger.html
- https://dev.mysql.com/doc/refman/8.0/en/create-event.html
- https://dev.mysql.com/doc/refman/8.0/en/create-server.html
- https://dev.mysql.com/doc/refman/8.0/en/create-tablespace.html
- https://dev.mysql.com/doc/refman/8.0/en/install-plugin.html
- https://dev.mysql.com/doc/refman/8.0/en/install-component.html
- https://dev.mysql.com/doc/refman/8.0/en/alter-instance.html

## Domain Decisions

- MySQL-migratable but syntax must be rewritten: `function`, `procedure`,
  `routine`, `trigger`, `user`, `role`, `server`, and `tablespace`.
- Rewrite intent rather than statement: `group` to role, `sequence` to
  `AUTO_INCREMENT` or helper table, `domain/type` to MySQL column type plus
  `CHECK`/`ENUM`/`SET`, `comment` to table/column comment clauses,
  `foreign_table` to FEDERATED table, `statistics` to `ANALYZE TABLE`
  histograms, `system` to `ALTER INSTANCE`/`SET PERSIST`, and materialized view
  intent to table plus event/procedure refresh.
- Do not migrate PostgreSQL-only DDL domains into MySQL references:
  `event_trigger`, `rule`, `operator`, `operator_class`, `operator_family`,
  `aggregate`, `cast`, `access_method`, `conversion`, `language`,
  `foreign_data_wrapper`, `foreign_schema`, `publication`, `subscription`,
  `security_label`, `large_object`, `transform`, `ownership`, and
  `text_search_*`.

## MySQL Missing Priority

P0:

- `CREATE/ALTER/DROP PROCEDURE`
- `CREATE/ALTER/DROP FUNCTION`
- `CREATE/DROP TRIGGER`
- `CREATE/ALTER/DROP EVENT`
- account statements already partly created in this migration
- `CREATE/ALTER/DROP SERVER`
- `CREATE/ALTER/DROP TABLESPACE`

P1:

- plugin/component/loadable function statements
- selected `ALTER INSTANCE` actions available in 8.0.22
- `CREATE/DROP SPATIAL REFERENCE SYSTEM`
- `CREATE/ALTER/DROP LOGFILE GROUP`

P2:

- `RENAME TABLE`
- resource group statements

Version exclusions: routine/trigger `IF NOT EXISTS` is 8.0.29+, `REVOKE IF
EXISTS` is 8.0.30+, `INSTALL COMPONENT ... SET` is 8.0.33+, and
`ALTER INSTANCE RELOAD KEYRING` is 8.0.24+.
