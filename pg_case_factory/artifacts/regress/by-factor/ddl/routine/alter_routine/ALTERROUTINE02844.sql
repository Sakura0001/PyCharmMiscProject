-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER ROUTINE extension_dependency=depends_on_nonexistent_extension
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERROUTINE02844
-- source_md: skills/pg-sql-generation/references/statements/ddl/routine/alter_routine.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/routine/alter_routine.yaml
-- primary_obligation_id: AR-EXT|02844|depends_on_extension|pg_aggregate_catalog|drop_aggregate
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PROCEDURE IF EXISTS alterroutine_02844_routine(integer) CASCADE;
DROP ROLE IF EXISTS alterroutine_02844_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE ROLE alterroutine_02844_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterroutine_02844_owner;
SET ROLE alterroutine_02844_owner;
CREATE PROCEDURE alterroutine_02844_routine(integer) LANGUAGE sql AS $$ SELECT 1 $$;
RESET ROLE;
SET ROLE alterroutine_02844_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER ROUTINE。
-- primary-target-begin
ALTER ROUTINE alterroutine_02844_routine DEPENDS ON EXTENSION alterroutine_02844_no_such_ext;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT p.proname, p.prokind FROM pg_catalog.pg_aggregate AS ag JOIN pg_catalog.pg_proc AS p ON p.oid = ag.aggfnoid WHERE p.proname = 'alterroutine_02844_routine' ORDER BY p.oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PROCEDURE IF EXISTS alterroutine_02844_routine(integer) CASCADE;
DROP PROCEDURE IF EXISTS alterroutine_02844_routine(integer) CASCADE;
DROP OWNED BY alterroutine_02844_owner;
DROP ROLE IF EXISTS alterroutine_02844_owner;
