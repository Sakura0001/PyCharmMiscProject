-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER ROUTINE owner_to_shape=membership_required_under_routine_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERROUTINE02292
-- source_md: skills/pg-sql-generation/references/statements/ddl/routine/alter_routine.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/routine/alter_routine.yaml
-- primary_obligation_id: AR-EXT|02292|owner|error_assertion|drop_function
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS alterroutine_02292_routine(integer) CASCADE;
DROP ROLE IF EXISTS alterroutine_02292_new_owner;
DROP ROLE IF EXISTS alterroutine_02292_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE ROLE alterroutine_02292_new_owner LOGIN;
CREATE ROLE alterroutine_02292_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterroutine_02292_owner;
SET ROLE alterroutine_02292_owner;
CREATE FUNCTION alterroutine_02292_routine(integer) RETURNS integer AS $$ SELECT 1 $$ LANGUAGE sql;
RESET ROLE;
SET ROLE alterroutine_02292_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER ROUTINE。
-- primary-target-begin
ALTER ROUTINE alterroutine_02292_routine OWNER TO alterroutine_02292_new_owner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT '42501' AS expected_sqlstate;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION IF EXISTS alterroutine_02292_routine(integer) CASCADE;
DROP FUNCTION IF EXISTS alterroutine_02292_routine(integer) CASCADE;
DROP OWNED BY alterroutine_02292_new_owner;
DROP ROLE IF EXISTS alterroutine_02292_new_owner;
DROP OWNED BY alterroutine_02292_owner;
DROP ROLE IF EXISTS alterroutine_02292_owner;
