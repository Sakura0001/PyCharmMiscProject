-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE FUNCTION language_not_available=untrusted_language_requires_superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEFUNCTION00065
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/create_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/create_function.yaml
-- primary_obligation_id: CFUNC-SFV|sfv-fac053d659f1a8183a09e866|create_function
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS createfunction_00065_fn(integer) CASCADE;
DROP TYPE IF EXISTS createfunction_00065_ctype CASCADE;
DROP TYPE IF EXISTS createfunction_00065_etype CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createfunction_00065_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createfunction_00065_actor LOGIN NOSUPERUSER;
SET ROLE createfunction_00065_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE FUNCTION。
-- primary-target-begin
CREATE FUNCTION createfunction_00065_fn(integer) RETURNS integer LANGUAGE c AS '$libdir/no_such_file', 'no_such_symbol';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS function_state FROM pg_catalog.pg_proc WHERE proname = 'createfunction_00065_fn' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION IF EXISTS createfunction_00065_fn(integer);
DROP OWNED BY createfunction_00065_actor CASCADE;
DROP ROLE IF EXISTS createfunction_00065_actor;
