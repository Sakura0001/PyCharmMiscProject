# MySQL 8.0 语句适配矩阵

本文以 MySQL 8.0 Reference Manual 第 15 章 SQL Statements 为准，记录官方语句分类、主要使用方式、当前工具覆盖状态、是否适合进入 `ddlcheck-mysql` 的 `STRESS` 路径，以及验证证据。

官方来源：

- [SQL Statements](https://dev.mysql.com/doc/refman/8.0/en/sql-statements.html)
- [Data Definition Statements](https://dev.mysql.com/doc/refman/8.0/en/sql-data-definition-statements.html)
- [Data Manipulation Statements](https://dev.mysql.com/doc/refman/8.0/en/sql-data-manipulation-statements.html)
- [Transactional and Locking Statements](https://dev.mysql.com/doc/refman/8.0/en/sql-transactional-statements.html)
- [Replication Statements](https://dev.mysql.com/doc/refman/8.0/en/sql-replication-statements.html)
- [Prepared Statements](https://dev.mysql.com/doc/refman/8.0/en/sql-prepared-statements.html)
- [Compound Statement Syntax](https://dev.mysql.com/doc/refman/8.0/en/sql-compound-statements.html)
- [Database Administration Statements](https://dev.mysql.com/doc/refman/8.0/en/sql-server-administration-statements.html)
- [Utility Statements](https://dev.mysql.com/doc/refman/8.0/en/sql-utility-statements.html)

## Decision Legend

| Decision | Meaning |
|---|---|
| Adapt | Suitable for random or semi-random `STRESS` execution. |
| Cautious | Useful, but should be low weight, generated through a constrained helper, or tested in a scenario rather than as isolated SQL. |
| Manual only | Good target for a future focused test, but not for the default random stress loop. |
| Exclude | Do not generate in this tool by default. |

## Statement Matrix

| Official category | Statement family | Main usage forms | Decision | Reason | Current tool state | Target batch | Verification evidence |
|---|---|---|---|---|---|---|---|
| DDL | Table DDL | `CREATE TABLE`, `ALTER TABLE`, `DROP TABLE`, `RENAME TABLE`, `TRUNCATE TABLE` | Adapt | Core schema mutation workload for this tool. | Already in `MySQLDDLStmt` and `mysql.grammar.yy`. | Existing + batch 0 docs | Covered by compile, grammar tests, STRESS logs. |
| DDL | Index DDL | `CREATE INDEX`, `DROP INDEX`, `ALTER TABLE ADD/DROP/RENAME INDEX` | Adapt | High-value schema/index churn. | Already in DDL enum and grammar. | Existing + batch 0 docs | Covered by grammar tests and STRESS logs. |
| DDL | View DDL | `CREATE VIEW`, `ALTER VIEW`, `DROP VIEW` | Cautious | Useful, but depends on SELECT stability and view metadata. | Already in DDL enum and grammar. | Existing + batch 0 docs | Covered by grammar tests and STRESS logs. |
| DDL | Database DDL | `CREATE DATABASE`, `ALTER DATABASE`, `DROP DATABASE` | Manual only | Framework already owns per-test database lifecycle. Random generation would break isolation. | Not a random SQL root. | Exclude from random path | Documented exclusion. |
| DDL | Routine, event, trigger | `CREATE/ALTER/DROP PROCEDURE`, `FUNCTION`, `EVENT`, `TRIGGER` | Manual only | Requires stored program context and stable body generation. | Not in MySQL STRESS path. | Future focused mode | Documented as non-default. |
| DDL | Tablespace/logfile/server/SRS/instance | `CREATE/ALTER/DROP TABLESPACE`, logfile group, server, SRS, `ALTER INSTANCE` | Exclude except existing gated tablespace subset | Strong engine, file, privilege, and instance-level dependencies. | Existing Dstore tablespace subset has a gate. | Existing gated subset only | Any tablespace failure must be checked in logs. |
| DML | Query | `SELECT`, joins, subqueries, CTE, grouping, ordering, limiting | Adapt | Main read workload and query planner surface. | STRESS `QUERY` pool now keeps `SELECT` and wraps some generated SELECTs with `EXPLAIN`. | Batch 1 done | `codexdone_*` live logs show `[kind=QUERY] SELECT` and `EXPLAIN`. |
| DML | Read-only metadata query | `EXPLAIN SELECT`, `DESCRIBE table`, safe `SHOW` metadata | Adapt | Useful low-risk statement coverage. | STRESS query pool now includes `DESCRIBE`, `SHOW TABLES`, `SHOW COLUMNS`, `SHOW INDEX`, `SHOW CREATE TABLE`. | Batch 1 done | `codexdone_*` live logs show EXPLAIN, DESCRIBE, SHOW metadata. |
| DML | Row mutation | `INSERT`, `REPLACE`, `UPDATE`, `DELETE` | Adapt | Main data mutation workload. | STRESS uses hand-written safe DML, not grammar DML. | Existing + batch 4 | DML tests and live logs. |
| DML | Extended DML | multi-row insert, `INSERT ... SELECT`, predicates, `ON DUPLICATE KEY UPDATE` | Cautious | Valuable, but must avoid generated columns and FK parent deletes. | STRESS helper now includes controlled multi-row `INSERT IGNORE`, `INSERT IGNORE ... SELECT`, predicate `UPDATE/DELETE LIMIT 1`, and `INSERT ... ON DUPLICATE KEY UPDATE`. | Batch 4 done | `TestMySQLStressDML` and `codexdone_*` live logs. |
| DML | File import/export | `LOAD DATA`, `LOAD XML`, `IMPORT TABLE`, `SELECT ... INTO OUTFILE/DUMPFILE` | Exclude | File-system, privilege, and server/client path dependent. | Not generated. | Exclude | Documented exclusion. |
| Transactional and locking | Transaction control | `START TRANSACTION`, `BEGIN`, `COMMIT`, `ROLLBACK` | Cautious | Useful only as a closed scenario; isolated random transaction statements are unstable. | Short STRESS transaction scenario now uses `START TRANSACTION` and closes with `COMMIT` or `ROLLBACK`; DDL is not used in the scenario. | Batch 3 done | `TestMySQLStressTransactionScenario` and live transaction logs. |
| Transactional and locking | Savepoint | `SAVEPOINT`, `ROLLBACK TO SAVEPOINT`, `RELEASE SAVEPOINT` | Cautious | Useful in short scenario inside a transaction. | Short STRESS transaction scenario now creates, rolls back to, and releases savepoints when prior DML succeeds. | Batch 3 done | Unit test covers closed sequence and failed-DML rollback; live logs show savepoint sequence. |
| Transactional and locking | Isolation | `SET SESSION TRANSACTION ISOLATION LEVEL ...` | Cautious | Session-scoped only; no global changes. | `set_isolation` root exists but is not used by STRESS. | Batch 3 or later | Scenario-only evidence. |
| Transactional and locking | Table and instance locks | `LOCK TABLES`, `UNLOCK TABLES`, `LOCK INSTANCE FOR BACKUP` | Manual only / Exclude | May block concurrent workers or affect the whole instance. | Not generated. | Exclude default random path | Documented exclusion. |
| Replication | Source, replica, group replication | `CHANGE REPLICATION SOURCE TO`, `START/STOP REPLICA`, `RESET REPLICA`, group replication statements | Exclude | Requires replication topology and changes server state. | Not generated. | Exclude | Documented exclusion. |
| Prepared statements | Prepared lifecycle | `PREPARE`, `EXECUTE`, `DEALLOCATE PREPARE` | Manual only | Useful, but needs lifecycle and variable management. | Not generated. | Future focused mode | Documented non-default. |
| Compound statements | Stored program body | `BEGIN ... END`, `DECLARE`, `IF`, `LOOP`, cursor, handler, `SIGNAL` | Manual only | Valid mainly inside stored programs, not standalone random SQL. | Not generated. | Future focused mode | Documented non-default. |
| Administration | Table maintenance | `ANALYZE TABLE`, `CHECK TABLE`, `CHECKSUM TABLE`, `OPTIMIZE TABLE`, `REPAIR TABLE` | Adapt / Cautious | Good stress coverage; heavy or engine-specific statements should be low weight. | Low-weight STRESS maintenance pool now includes all five table maintenance statements. | Batch 2 done | `TestMySQLStressQueryAndMaintenancePool` and live logs show `[kind=MAINTENANCE]`. |
| Administration | Session variables | safe `SET SESSION ...`, `SET NAMES`, `SET CHARACTER SET` | Cautious | Session-scoped values can be useful; global/persist is excluded. | `set_variable` exists but includes global choices and is not used by STRESS. | Future whitelist | Documented caution. |
| Administration | Account/DCL/security/resource/plugin/component/clone/server control | `CREATE USER`, `GRANT`, `REVOKE`, roles, plugins, components, clone, `KILL`, `RESTART`, `SHUTDOWN` | Exclude | Security, topology, OS, or server-lifecycle side effects. | Not generated in default path. | Exclude | Documented exclusion. |
| Administration | `FLUSH`/`RESET` | `FLUSH`, `RESET`, `RESET PERSIST` | Exclude by default | Many forms are global, lock-heavy, replication-related, or persistent. | Roots exist but are not used by STRESS. | Exclude default random path | Documented exclusion. |
| Utility | Context and inspection | `USE`, `EXPLAIN`, `DESCRIBE`, `HELP` | Adapt safe inspection only | `USE` is owned by framework DB setup; `HELP` depends on help tables. | `USE` remains framework-owned; `EXPLAIN` and `DESCRIBE` are in the STRESS query pool. | Batch 1 done | `codexdone_*` live logs show EXPLAIN/DESCRIBE. |

## Verification Record

Each implementation batch must update this section with:

- compile command and result,
- static test command and result,
- live MySQL command and result,
- `logs/mysql/*-cur.log` evidence,
- any `logs/mysql/*.log` finding and root-cause analysis.

Current implementation verification on this branch:

- Compile passed:
  `javac -proc:none -cp 'libs/*:src/main/resources' -d build/classes $(find src/main/java -name '*.java')`
  and test compile passed with `build/TestReflectionRunner.java`.
- Static tests passed:
  `TestGlobalStateResourceLoading`, `TestJdbcDrivers`, MySQL connection URL, grammar/type support, stress generation regression, virtual column coverage, tablespace support/gate, stress oracle config/execution behavior, `TestMySQLStressDML`, `TestMySQLStressQueryAndMaintenancePool`, and `TestMySQLStressTransactionScenario`.
- Local MySQL verified:
  `127.0.0.1:3306 root/Taurus_123`, server version `8.0.45 Homebrew`.
- Small live STRESS passed with prefix `codexdone_smoke_`:
  `success=57 fail=6 total=63 rate=90.48%`; no framework `.log`; evidence included `ON DUPLICATE KEY UPDATE`, multi-row insert, maintenance, transaction/savepoint, EXPLAIN/DESCRIBE/SHOW.
- Single-thread live STRESS passed with prefix `codexdone_single_`:
  `success=286 fail=62 total=348 rate=82.18%`; counts were DDL 60, DML 120, MAINTENANCE 12, QUERY 120, TRANSACTION 36; no framework `.log`, no `code=1305`, no worker-level failures.
- Multi-thread live STRESS passed with prefix `codexdone_mt_`:
  `success=1570 fail=286 total=1856 rate=84.59%`; current inspectable logs are `logs/mysql/codexdone_mt_0-cur.log` and `logs/mysql/codexdone_mt_1-cur.log`; counts were DDL 320, DML 640, MAINTENANCE 64, QUERY 640, TRANSACTION 192 across two databases and eight worker threads per log.
- Log acceptance:
  `find logs/mysql -maxdepth 1 -name '*.log' ! -name '*-cur.log'` returned no files.
  `rg 'code=1305|Worker failed|Retry also failed' logs/mysql/codexdone_mt_*-cur.log` returned no matches.
  Negative scan for DCL, replication, plugin/component, server lifecycle, file-system, global/persistent configuration, and backup lock statements returned no matches.
- `FAIL(code=...)` attribution:
  remaining failures are ordinary SQL semantics, concurrency, or schema-churn effects: duplicate/missing objects, unsupported online DDL algorithms, generated-column and functional-index constraints, FK incompatibility, data truncation/out-of-range values, deadlocks, `ONLY_FULL_GROUP_BY`, invalid generated SELECT placement such as `SQL_BUFFER_RESULT`, and subqueries returning more than one row. No unexplained framework exception log was produced.

Existing worktree note before this branch work:

- The worktree already had local modifications in `mysql.grammar.yy`, `TestMySQLEDCOracle.java`, and `TestMySQLGrammarAndTypeSupport.java`; this adaptation preserved them.
