-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER FUNCTION object_state=not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFUNCTION12371
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/alter_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/alter_function.yaml
-- primary_obligation_id: AF-EXT|12371|called_on_null_input|pg_get_functiondef|DROP_FUNCTION_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42883
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS residual_check_no_objects;
\set ON_ERROR_STOP on
-- 2. 创建完整本地函数和因子专用夹具。
SELECT 1 AS target_routine_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER FUNCTION。
-- primary-target-begin
ALTER FUNCTION alterfunction_12371_fn CALLED ON NULL INPUT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42883' AS target_sqlstate_matches_expected;
SELECT pg_get_functiondef(p.oid) FROM pg_catalog.pg_proc AS p WHERE p.proname = 'alterfunction_12371_fn' ORDER BY p.oid;
-- 5. 清理全部本编号对象。
SELECT 1 AS residual_check_no_objects;
