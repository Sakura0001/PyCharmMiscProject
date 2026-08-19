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
-- case_id: ALTERFUNCTION05172
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/alter_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/alter_function.yaml
-- primary_obligation_id: AF-EXT|05172|rename|pg_get_functiondef|DROP_FUNCTION_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42883
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS alterfunction_05172_owner;
DROP SCHEMA IF EXISTS alterfunction_05172_src_schema CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地函数和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS alterfunction_05172_src_schema;
CREATE ROLE alterfunction_05172_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterfunction_05172_owner;
GRANT CREATE ON SCHEMA alterfunction_05172_src_schema TO alterfunction_05172_owner;
GRANT USAGE ON SCHEMA alterfunction_05172_src_schema TO alterfunction_05172_owner;
SET ROLE alterfunction_05172_owner;
SELECT 1 AS target_routine_intentionally_absent;
RESET ROLE;
SET ROLE alterfunction_05172_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER FUNCTION。
-- primary-target-begin
ALTER FUNCTION alterfunction_05172_src_schema.alterfunction_05172_fn(integer) RENAME TO alterfunction_05172_renamed;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42883' AS target_sqlstate_matches_expected;
SELECT pg_get_functiondef(p.oid) FROM pg_catalog.pg_proc AS p WHERE p.proname = 'alterfunction_05172_fn' ORDER BY p.oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY alterfunction_05172_owner;
DROP ROLE IF EXISTS alterfunction_05172_owner;
DROP SCHEMA IF EXISTS alterfunction_05172_src_schema CASCADE;
