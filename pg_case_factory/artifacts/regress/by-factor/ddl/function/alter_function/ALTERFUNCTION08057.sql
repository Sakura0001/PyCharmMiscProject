-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER FUNCTION new_name_shape=simple
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFUNCTION08057
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/alter_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/alter_function.yaml
-- primary_obligation_id: AF-EXT|08057|rename|information_schema_routines|DROP_FUNCTION_IF_EXISTS
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS "alterfunction_08057_select"(integer) CASCADE;
DROP FUNCTION IF EXISTS alterfunction_08057_renamed(integer) CASCADE;
DROP ROLE IF EXISTS alterfunction_08057_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地函数和因子专用夹具。
CREATE ROLE alterfunction_08057_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterfunction_08057_owner;
SET ROLE alterfunction_08057_owner;
CREATE FUNCTION "alterfunction_08057_select"(integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE sql;
RESET ROLE;
SET ROLE alterfunction_08057_owner;
-- 3. 执行唯一获得覆盖信用的 ALTER FUNCTION。
-- primary-target-begin
ALTER FUNCTION "alterfunction_08057_select"(integer) RENAME TO alterfunction_08057_renamed;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT r.routine_schema, r.routine_name, r.routine_type FROM information_schema.routines AS r WHERE r.routine_name = 'alterfunction_08057_renamed' ORDER BY r.routine_schema, r.routine_name;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION IF EXISTS alterfunction_08057_renamed(integer);
DROP FUNCTION IF EXISTS "alterfunction_08057_select"(integer) CASCADE;
DROP FUNCTION IF EXISTS alterfunction_08057_renamed(integer) CASCADE;
DROP OWNED BY alterfunction_08057_owner;
DROP ROLE IF EXISTS alterfunction_08057_owner;
