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
-- case_id: ALTERFUNCTION10339
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/alter_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/alter_function.yaml
-- primary_obligation_id: AF-EXT|10339|immutable|pg_proc_catalog_query|DROP_FUNCTION
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS "alterfunction_10339_Mixed Function"(integer) CASCADE;
DROP ROLE IF EXISTS alterfunction_10339_alter;
DROP ROLE IF EXISTS alterfunction_10339_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地函数和因子专用夹具。
CREATE ROLE alterfunction_10339_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterfunction_10339_owner;
CREATE ROLE alterfunction_10339_alter LOGIN;
SET ROLE alterfunction_10339_owner;
CREATE FUNCTION "alterfunction_10339_Mixed Function"(integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE sql;
GRANT EXECUTE ON FUNCTION "alterfunction_10339_Mixed Function"(integer) TO alterfunction_10339_alter;
RESET ROLE;
SET ROLE alterfunction_10339_alter;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER FUNCTION。
-- primary-target-begin
ALTER FUNCTION "alterfunction_10339_Mixed Function" IMMUTABLE RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT p.provolatile, p.prokind, p.prosecdef, p.proleakproof, p.proparallel, p.procost, p.prorows FROM pg_catalog.pg_proc AS p WHERE p.proname = 'alterfunction_10339_Mixed Function' ORDER BY p.proname, p.oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION "alterfunction_10339_Mixed Function"(integer);
DROP FUNCTION IF EXISTS "alterfunction_10339_Mixed Function"(integer) CASCADE;
DROP OWNED BY alterfunction_10339_alter;
DROP ROLE IF EXISTS alterfunction_10339_alter;
DROP OWNED BY alterfunction_10339_owner;
DROP ROLE IF EXISTS alterfunction_10339_owner;
