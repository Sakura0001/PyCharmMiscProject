-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER ROUTINE routine_state=non_existent
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERROUTINE02857
-- source_md: skills/pg-sql-generation/references/statements/ddl/routine/alter_routine.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/routine/alter_routine.yaml
-- primary_obligation_id: AR-EXT|02857|depends_on_extension|pg_proc_catalog|drop_function
-- expected_outcome: expected_failure
-- expected_sqlstate: 42883
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS alterroutine_02857_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE ROLE alterroutine_02857_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterroutine_02857_owner;
SET ROLE alterroutine_02857_owner;
SELECT 1 AS target_routine_intentionally_absent;
RESET ROLE;
SET ROLE alterroutine_02857_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER ROUTINE。
-- primary-target-begin
ALTER ROUTINE alterroutine_02857_routine DEPENDS ON EXTENSION plpgsql;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42883' AS target_sqlstate_matches_expected;
SELECT p.proname, p.prokind, p.proowner::regrole, p.proleakproof, p.prosecdef, p.proparallel FROM pg_catalog.pg_proc AS p WHERE p.proname = 'alterroutine_02857_routine' ORDER BY p.proname, p.oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY alterroutine_02857_owner;
DROP ROLE IF EXISTS alterroutine_02857_owner;
