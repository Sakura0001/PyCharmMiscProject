-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER ROUTINE executor_privilege=non_owner_with_grant_option
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERROUTINE01524
-- source_md: skills/pg-sql-generation/references/statements/ddl/routine/alter_routine.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/routine/alter_routine.yaml
-- primary_obligation_id: AR-EXT|01524|owner|pg_aggregate_catalog|drop_aggregate
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PROCEDURE IF EXISTS alterroutine_01524_routine(integer) CASCADE;
DROP ROLE IF EXISTS alterroutine_01524_alter;
DROP ROLE IF EXISTS alterroutine_01524_new_owner;
DROP ROLE IF EXISTS alterroutine_01524_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE ROLE alterroutine_01524_new_owner LOGIN;
CREATE ROLE alterroutine_01524_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterroutine_01524_owner;
CREATE ROLE alterroutine_01524_alter LOGIN;
SET ROLE alterroutine_01524_owner;
CREATE PROCEDURE alterroutine_01524_routine(integer) LANGUAGE sql AS $$ SELECT 1 $$;
GRANT EXECUTE ON PROCEDURE alterroutine_01524_routine(integer) TO alterroutine_01524_alter;
RESET ROLE;
SET ROLE alterroutine_01524_alter;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER ROUTINE。
-- primary-target-begin
ALTER ROUTINE alterroutine_01524_routine OWNER TO alterroutine_01524_new_owner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT p.proname, p.prokind FROM pg_catalog.pg_aggregate AS ag JOIN pg_catalog.pg_proc AS p ON p.oid = ag.aggfnoid WHERE p.proname = 'alterroutine_01524_routine' ORDER BY p.oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PROCEDURE IF EXISTS alterroutine_01524_routine(integer) CASCADE;
DROP PROCEDURE IF EXISTS alterroutine_01524_routine(integer) CASCADE;
DROP OWNED BY alterroutine_01524_alter;
DROP ROLE IF EXISTS alterroutine_01524_alter;
DROP OWNED BY alterroutine_01524_new_owner;
DROP ROLE IF EXISTS alterroutine_01524_new_owner;
DROP OWNED BY alterroutine_01524_owner;
DROP ROLE IF EXISTS alterroutine_01524_owner;
