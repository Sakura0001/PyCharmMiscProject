-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER FUNCTION object_state=different_signature_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFUNCTION03853
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/alter_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/alter_function.yaml
-- primary_obligation_id: AF-EXT|03853|called_on_null_input|information_schema_routines|DROP_FUNCTION
-- expected_outcome: expected_failure
-- expected_sqlstate: 42883
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS alterfunction_03853_src_schema.alterfunction_03853_fn(integer) CASCADE;
DROP SCHEMA IF EXISTS alterfunction_03853_src_schema CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地函数和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS alterfunction_03853_src_schema;
CREATE FUNCTION alterfunction_03853_src_schema.alterfunction_03853_fn(integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE sql;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER FUNCTION。
-- primary-target-begin
ALTER FUNCTION alterfunction_03853_src_schema.alterfunction_03853_fn(integer, text) CALLED ON NULL INPUT RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42883' AS target_sqlstate_matches_expected;
SELECT r.routine_schema, r.routine_name, r.routine_type FROM information_schema.routines AS r WHERE r.routine_name = 'alterfunction_03853_fn' ORDER BY r.routine_schema, r.routine_name;
-- 5. 清理全部本编号对象。
DROP FUNCTION alterfunction_03853_src_schema.alterfunction_03853_fn(integer);
DROP FUNCTION IF EXISTS alterfunction_03853_src_schema.alterfunction_03853_fn(integer) CASCADE;
DROP SCHEMA IF EXISTS alterfunction_03853_src_schema CASCADE;
