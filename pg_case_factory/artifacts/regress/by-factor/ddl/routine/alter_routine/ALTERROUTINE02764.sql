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
-- case_id: ALTERROUTINE02764
-- source_md: skills/pg-sql-generation/references/statements/ddl/routine/alter_routine.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/routine/alter_routine.yaml
-- primary_obligation_id: AR-EXT|02764|set_schema|pg_aggregate_catalog|drop_aggregate
-- expected_outcome: expected_failure
-- expected_sqlstate: 42883
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS alterroutine_02764_owner;
DROP SCHEMA IF EXISTS alterroutine_02764_dst_schema CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS alterroutine_02764_dst_schema;
CREATE ROLE alterroutine_02764_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterroutine_02764_owner;
GRANT CREATE ON SCHEMA alterroutine_02764_dst_schema TO alterroutine_02764_owner;
GRANT USAGE ON SCHEMA alterroutine_02764_dst_schema TO alterroutine_02764_owner;
SET ROLE alterroutine_02764_owner;
SELECT 1 AS target_routine_intentionally_absent;
RESET ROLE;
SET ROLE alterroutine_02764_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER ROUTINE。
-- primary-target-begin
ALTER ROUTINE alterroutine_02764_routine SET SCHEMA alterroutine_02764_dst_schema;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42883' AS target_sqlstate_matches_expected;
SELECT p.proname, p.prokind FROM pg_catalog.pg_aggregate AS ag JOIN pg_catalog.pg_proc AS p ON p.oid = ag.aggfnoid WHERE p.proname = 'alterroutine_02764_routine' ORDER BY p.oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY alterroutine_02764_owner;
DROP ROLE IF EXISTS alterroutine_02764_owner;
DROP SCHEMA IF EXISTS alterroutine_02764_dst_schema CASCADE;
