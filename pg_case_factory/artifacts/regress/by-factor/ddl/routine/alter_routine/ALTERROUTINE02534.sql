-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER ROUTINE new_name_shape=existing_name_conflict
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERROUTINE02534
-- source_md: skills/pg-sql-generation/references/statements/ddl/routine/alter_routine.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/routine/alter_routine.yaml
-- primary_obligation_id: AR-EXT|02534|rename|error_assertion|drop_aggregate
-- expected_outcome: expected_failure
-- expected_sqlstate: 42723
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS alterroutine_02534_routine(integer) CASCADE;
DROP ROLE IF EXISTS alterroutine_02534_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE ROLE alterroutine_02534_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterroutine_02534_owner;
SET ROLE alterroutine_02534_owner;
CREATE FUNCTION alterroutine_02534_routine(integer) RETURNS integer AS $$ SELECT 1 $$ LANGUAGE sql;
CREATE FUNCTION alterroutine_02534_dup_routine(integer) LANGUAGE sql AS $$ SELECT 1 $$;
RESET ROLE;
SET ROLE alterroutine_02534_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER ROUTINE。
-- primary-target-begin
ALTER ROUTINE alterroutine_02534_routine RENAME TO alterroutine_02534_dup_routine;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42723' AS target_sqlstate_matches_expected;
SELECT '42723' AS expected_sqlstate;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION IF EXISTS alterroutine_02534_routine(integer) CASCADE;
DROP FUNCTION IF EXISTS alterroutine_02534_routine(integer) CASCADE;
DROP OWNED BY alterroutine_02534_owner;
DROP ROLE IF EXISTS alterroutine_02534_owner;
