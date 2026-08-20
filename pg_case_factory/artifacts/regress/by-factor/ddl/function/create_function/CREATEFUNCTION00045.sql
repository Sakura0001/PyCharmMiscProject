-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE FUNCTION expected_status=failure
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEFUNCTION00045
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/create_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/create_function.yaml
-- primary_obligation_id: CFUNC-SFV|sfv-f271283e33bdf12641ec7e9c|create_function
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS createfunction_00045_fn(integer) CASCADE;
DROP TYPE IF EXISTS createfunction_00045_ctype CASCADE;
DROP TYPE IF EXISTS createfunction_00045_etype CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createfunction_00045_fn(integer) RETURNS integer LANGUAGE sql RETURN $1;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE FUNCTION。
-- primary-target-begin
CREATE FUNCTION createfunction_00045_fn(integer) RETURNS integer LANGUAGE sql RETURN $1;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS function_state FROM pg_catalog.pg_proc WHERE proname = 'createfunction_00045_fn' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP FUNCTION IF EXISTS createfunction_00045_fn(integer);
