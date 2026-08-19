-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER FUNCTION object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFUNCTION07651
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/alter_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/alter_function.yaml
-- primary_obligation_id: AF-EXT|07651|set_schema|information_schema_routines|DROP_FUNCTION
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS "alterfunction_07651_Mixed Function"(integer) CASCADE;
DROP FUNCTION IF EXISTS alterfunction_07651_dst_schema."alterfunction_07651_Mixed Function"(integer) CASCADE;
DROP ROLE IF EXISTS alterfunction_07651_owner;
DROP SCHEMA IF EXISTS alterfunction_07651_dst_schema CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地函数和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS alterfunction_07651_dst_schema;
CREATE ROLE alterfunction_07651_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterfunction_07651_owner;
GRANT CREATE ON SCHEMA alterfunction_07651_dst_schema TO alterfunction_07651_owner;
GRANT USAGE ON SCHEMA alterfunction_07651_dst_schema TO alterfunction_07651_owner;
SET ROLE alterfunction_07651_owner;
CREATE FUNCTION "alterfunction_07651_Mixed Function"(integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE sql;
RESET ROLE;
SET ROLE alterfunction_07651_owner;
-- 3. 执行唯一获得覆盖信用的 ALTER FUNCTION。
-- primary-target-begin
ALTER FUNCTION "alterfunction_07651_Mixed Function"(integer) SET SCHEMA alterfunction_07651_dst_schema;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT r.routine_schema, r.routine_name, r.routine_type FROM information_schema.routines AS r WHERE r.routine_name = 'alterfunction_07651_Mixed Function' ORDER BY r.routine_schema, r.routine_name;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION alterfunction_07651_dst_schema."alterfunction_07651_Mixed Function"(integer);
DROP FUNCTION IF EXISTS "alterfunction_07651_Mixed Function"(integer) CASCADE;
DROP FUNCTION IF EXISTS alterfunction_07651_dst_schema."alterfunction_07651_Mixed Function"(integer) CASCADE;
DROP OWNED BY alterfunction_07651_owner;
DROP ROLE IF EXISTS alterfunction_07651_owner;
DROP SCHEMA IF EXISTS alterfunction_07651_dst_schema CASCADE;
