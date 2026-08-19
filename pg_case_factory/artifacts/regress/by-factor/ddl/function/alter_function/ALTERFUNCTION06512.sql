-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER FUNCTION rename_target=duplicate_name
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFUNCTION06512
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/alter_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/alter_function.yaml
-- primary_obligation_id: AF-EXT|06512|rename|pg_get_functiondef|DROP_FUNCTION_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42723
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS alterfunction_06512_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterfunction_06512_dup_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterfunction_06512_dup_fn(integer) CASCADE;
DROP ROLE IF EXISTS alterfunction_06512_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地函数和因子专用夹具。
CREATE ROLE alterfunction_06512_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterfunction_06512_owner;
SET ROLE alterfunction_06512_owner;
CREATE FUNCTION alterfunction_06512_fn(integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE sql;
CREATE FUNCTION alterfunction_06512_dup_fn(integer) RETURNS integer AS $$ SELECT 1 $$ LANGUAGE sql;
RESET ROLE;
SET ROLE alterfunction_06512_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER FUNCTION。
-- primary-target-begin
ALTER FUNCTION alterfunction_06512_fn(integer) RENAME TO alterfunction_06512_dup_fn;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42723' AS target_sqlstate_matches_expected;
SELECT pg_get_functiondef(p.oid) FROM pg_catalog.pg_proc AS p WHERE p.proname = 'alterfunction_06512_fn' ORDER BY p.oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION IF EXISTS alterfunction_06512_fn(integer);
DROP FUNCTION IF EXISTS alterfunction_06512_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterfunction_06512_dup_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterfunction_06512_dup_fn(integer) CASCADE;
DROP OWNED BY alterfunction_06512_owner;
DROP ROLE IF EXISTS alterfunction_06512_owner;
