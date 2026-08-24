-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER FUNCTION privilege_level=non_owner_with_alter
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFUNCTION00913
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/alter_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/alter_function.yaml
-- primary_obligation_id: AF-EXT|00913|volatile|pg_get_functiondef|DROP_FUNCTION
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS "alterfunction_00913_Mixed Function"(integer) CASCADE;
DROP ROLE IF EXISTS alterfunction_00913_alter;
DROP ROLE IF EXISTS alterfunction_00913_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地函数和因子专用夹具。
CREATE ROLE alterfunction_00913_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterfunction_00913_owner;
CREATE ROLE alterfunction_00913_alter LOGIN;
SET ROLE alterfunction_00913_owner;
CREATE FUNCTION "alterfunction_00913_Mixed Function"(integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE sql;
GRANT EXECUTE ON FUNCTION "alterfunction_00913_Mixed Function"(integer) TO alterfunction_00913_alter;
RESET ROLE;
SET ROLE alterfunction_00913_alter;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER FUNCTION。
-- primary-target-begin
ALTER FUNCTION "alterfunction_00913_Mixed Function"(integer) VOLATILE RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT pg_get_functiondef(p.oid) FROM pg_catalog.pg_proc AS p WHERE p.proname = 'alterfunction_00913_Mixed Function' ORDER BY p.oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION "alterfunction_00913_Mixed Function"(integer);
DROP FUNCTION IF EXISTS "alterfunction_00913_Mixed Function"(integer) CASCADE;
DROP OWNED BY alterfunction_00913_alter;
DROP ROLE IF EXISTS alterfunction_00913_alter;
DROP OWNED BY alterfunction_00913_owner;
DROP ROLE IF EXISTS alterfunction_00913_owner;
