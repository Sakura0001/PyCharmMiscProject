-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER FUNCTION owner_target=membership_required_under_function_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFUNCTION02947
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/alter_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/alter_function.yaml
-- primary_obligation_id: AF-EXT|02947|owner|pg_get_functiondef|DROP_FUNCTION
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS "alterfunction_02947_select"(integer) CASCADE;
DROP ROLE IF EXISTS alterfunction_02947_new_owner;
DROP ROLE IF EXISTS alterfunction_02947_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地函数和因子专用夹具。
CREATE ROLE alterfunction_02947_new_owner LOGIN;
CREATE ROLE alterfunction_02947_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterfunction_02947_owner;
SET ROLE alterfunction_02947_owner;
CREATE FUNCTION "alterfunction_02947_select"(integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE sql;
RESET ROLE;
SET ROLE alterfunction_02947_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER FUNCTION。
-- primary-target-begin
ALTER FUNCTION "alterfunction_02947_select"(integer) OWNER TO alterfunction_02947_new_owner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT pg_get_functiondef(p.oid) FROM pg_catalog.pg_proc AS p WHERE p.proname = 'alterfunction_02947_select' ORDER BY p.oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION "alterfunction_02947_select"(integer);
DROP FUNCTION IF EXISTS "alterfunction_02947_select"(integer) CASCADE;
DROP OWNED BY alterfunction_02947_new_owner;
DROP ROLE IF EXISTS alterfunction_02947_new_owner;
DROP OWNED BY alterfunction_02947_owner;
DROP ROLE IF EXISTS alterfunction_02947_owner;
