-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER ROUTINE routine_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERROUTINE03302
-- source_md: skills/pg-sql-generation/references/statements/ddl/routine/alter_routine.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/routine/alter_routine.yaml
-- primary_obligation_id: AR-EXT|03302|owner|pg_aggregate_catalog|drop_function
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE IF EXISTS alterroutine_03302_routine(integer) CASCADE;
DROP ROLE IF EXISTS alterroutine_03302_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE ROLE alterroutine_03302_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterroutine_03302_owner;
SET ROLE alterroutine_03302_owner;
CREATE AGGREGATE alterroutine_03302_routine(integer) (SFUNC = int4_sum, STYPE = bigint, INITCOND = '0');
RESET ROLE;
SET ROLE alterroutine_03302_owner;
-- 3. 执行唯一获得覆盖信用的 ALTER ROUTINE。
-- primary-target-begin
ALTER ROUTINE alterroutine_03302_routine OWNER TO SESSION_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT p.proname, p.prokind FROM pg_catalog.pg_aggregate AS ag JOIN pg_catalog.pg_proc AS p ON p.oid = ag.aggfnoid WHERE p.proname = 'alterroutine_03302_routine' ORDER BY p.oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP AGGREGATE IF EXISTS alterroutine_03302_routine(integer) CASCADE;
DROP AGGREGATE IF EXISTS alterroutine_03302_routine(integer) CASCADE;
DROP OWNED BY alterroutine_03302_owner;
DROP ROLE IF EXISTS alterroutine_03302_owner;
