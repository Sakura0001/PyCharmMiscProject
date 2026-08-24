-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER ROUTINE executor_privilege=non_owner_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERROUTINE00205
-- source_md: skills/pg-sql-generation/references/statements/ddl/routine/alter_routine.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/routine/alter_routine.yaml
-- primary_obligation_id: AR-EXT|00205|volatile|pg_aggregate_catalog|reset_config_parameter
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS alterroutine_00205_routine(integer) CASCADE;
DROP ROLE IF EXISTS alterroutine_00205_actor;
DROP ROLE IF EXISTS alterroutine_00205_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE ROLE alterroutine_00205_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterroutine_00205_owner;
CREATE ROLE alterroutine_00205_actor LOGIN;
GRANT USAGE ON SCHEMA public TO alterroutine_00205_actor;
SET ROLE alterroutine_00205_owner;
CREATE FUNCTION alterroutine_00205_routine(integer) RETURNS integer AS $$ SELECT 1 $$ LANGUAGE sql;
RESET ROLE;
SET ROLE alterroutine_00205_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER ROUTINE。
-- primary-target-begin
ALTER ROUTINE alterroutine_00205_routine VOLATILE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT p.proname, p.prokind FROM pg_catalog.pg_aggregate AS ag JOIN pg_catalog.pg_proc AS p ON p.oid = ag.aggfnoid WHERE p.proname = 'alterroutine_00205_routine' ORDER BY p.oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION IF EXISTS alterroutine_00205_routine(integer) CASCADE;
DROP FUNCTION IF EXISTS alterroutine_00205_routine(integer) CASCADE;
DROP OWNED BY alterroutine_00205_actor;
DROP ROLE IF EXISTS alterroutine_00205_actor;
DROP OWNED BY alterroutine_00205_owner;
DROP ROLE IF EXISTS alterroutine_00205_owner;
