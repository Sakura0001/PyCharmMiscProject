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
-- case_id: ALTERROUTINE01207
-- source_md: skills/pg-sql-generation/references/statements/ddl/routine/alter_routine.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/routine/alter_routine.yaml
-- primary_obligation_id: AR-EXT|01207|set_config_parameter|effect_query|drop_function
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS alterroutine_01207_routine(integer) CASCADE;
DROP ROLE IF EXISTS alterroutine_01207_alter;
DROP ROLE IF EXISTS alterroutine_01207_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE ROLE alterroutine_01207_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterroutine_01207_owner;
CREATE ROLE alterroutine_01207_alter LOGIN;
SET ROLE alterroutine_01207_owner;
CREATE FUNCTION alterroutine_01207_routine(integer) RETURNS integer AS $$ SELECT 1 $$ LANGUAGE sql;
GRANT EXECUTE ON FUNCTION alterroutine_01207_routine(integer) TO alterroutine_01207_alter;
RESET ROLE;
SET ROLE alterroutine_01207_alter;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER ROUTINE。
-- primary-target-begin
ALTER ROUTINE alterroutine_01207_routine SET alterroutine_01207_work_mem TO 100 RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT p.proname, p.prokind, p.proleakproof, p.prosecdef, p.proparallel, p.procost, p.prorows FROM pg_catalog.pg_proc AS p WHERE p.proname = 'alterroutine_01207_routine' ORDER BY p.proname, p.oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION IF EXISTS alterroutine_01207_routine(integer) CASCADE;
DROP FUNCTION IF EXISTS alterroutine_01207_routine(integer) CASCADE;
DROP OWNED BY alterroutine_01207_alter;
DROP ROLE IF EXISTS alterroutine_01207_alter;
DROP OWNED BY alterroutine_01207_owner;
DROP ROLE IF EXISTS alterroutine_01207_owner;
