# Stored Objects, Server Metadata, and Instance-Level Review

Target: MySQL Community Server 8.0.22.

Official sources:
- https://dev.mysql.com/doc/refman/8.0/en/create-procedure.html
- https://dev.mysql.com/doc/refman/8.0/en/alter-procedure.html
- https://dev.mysql.com/doc/refman/8.0/en/alter-function.html
- https://dev.mysql.com/doc/refman/8.0/en/drop-procedure.html
- https://dev.mysql.com/doc/refman/8.0/en/create-trigger.html
- https://dev.mysql.com/doc/refman/8.0/en/drop-trigger.html
- https://dev.mysql.com/doc/refman/8.0/en/create-event.html
- https://dev.mysql.com/doc/refman/8.0/en/alter-event.html
- https://dev.mysql.com/doc/refman/8.0/en/drop-event.html
- https://dev.mysql.com/doc/refman/8.0/en/sql-data-definition-statements.html
- https://dev.mysql.com/doc/refman/8.0/en/install-component.html
- https://dev.mysql.com/doc/refman/8.0/en/alter-instance.html

## Decisions

| Area | Decision |
|---|---|
| Stored procedures | Keep and rewrite to MySQL `CREATE/ALTER/DROP PROCEDURE`. `CREATE PROCEDURE IF NOT EXISTS` is excluded for 8.0.22. |
| Stored functions | Keep and rewrite to MySQL stored `CREATE/ALTER/DROP FUNCTION`. Loadable functions are tracked by plugin/loadable-function work, not routine references. |
| Routine umbrella | Drop `ALTER ROUTINE` and `DROP ROUTINE`; MySQL has no statement by those names. |
| Triggers | Keep `CREATE TRIGGER` and `DROP TRIGGER`, but remove PostgreSQL statement-level, constraint, `INSTEAD OF`, `TRUNCATE`, and trigger-function factors. MySQL 8.0.22 does not include `CREATE TRIGGER IF NOT EXISTS`. |
| PostgreSQL event triggers | Drop. MySQL `EVENT` is a scheduler object, not a DDL hook. |
| MySQL Event Scheduler | Add `CREATE/ALTER/DROP EVENT` from official MySQL syntax. |
| FEDERATED server metadata | Add `CREATE/ALTER/DROP SERVER`; mark privilege and metadata-only behavior. |
| Tablespaces | Add `CREATE/ALTER/DROP TABLESPACE`; separate InnoDB general/undo coverage from NDB-only or filesystem-sensitive cases. |
| Logfile groups | Add `CREATE/ALTER/DROP LOGFILE GROUP` as NDB-only references with default skip/negative execution modes. |
| Plugin and component administration | Add `INSTALL/UNINSTALL PLUGIN` and `INSTALL/UNINSTALL COMPONENT`; default to safe negative or isolated execution because these load code and modify server metadata. Exclude `INSTALL COMPONENT ... SET`, which is newer than 8.0.22. |
| Instance actions | Add 8.0.22 `ALTER INSTANCE` branches for redo log, key rotation, binlog key rotation, and TLS reload. Exclude `RELOAD KEYRING`, added later. |
| Resource groups | Add `CREATE/ALTER/DROP/SET RESOURCE GROUP`; mark platform, privilege, and thread-assignment risks. |
| Spatial reference systems | Add `CREATE/DROP SPATIAL REFERENCE SYSTEM`; track SRID range, reserved/builtin dependencies, and WKT validity. |
| Rename table | Add `RENAME TABLE` for single, multi-table, swap, cross-schema, and dependency-sensitive rename coverage. |

## Execution Policy

The fourth batch deliberately separates syntax coverage from runnable default cases. Routine, trigger, event, server metadata, rename table, and user-defined SRS can be generated as normal or metadata-only cases. The following branches are present as factors but should not be executed by default outside an isolated server: plugin/component install and uninstall, key rotation, TLS reload, redo log disablement, NDB logfile groups, NDB tablespace variants, tablespace file-path manipulation, forced resource-group operations, and dropping builtin or dependency-bound SRS IDs.
