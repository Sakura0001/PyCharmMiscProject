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
-- case_id: ALTERFUNCTION05661
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/alter_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/alter_function.yaml
-- primary_obligation_id: AF-EXT|05661|leakproof|pg_proc_catalog_query|DROP_FUNCTION_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS alterfunction_05661_fn(integer) CASCADE;
DROP ROLE IF EXISTS alterfunction_05661_alter;
DROP ROLE IF EXISTS alterfunction_05661_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地函数和因子专用夹具。
CREATE ROLE alterfunction_05661_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterfunction_05661_owner;
CREATE ROLE alterfunction_05661_alter LOGIN;
SET ROLE alterfunction_05661_owner;
CREATE FUNCTION alterfunction_05661_fn(integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE sql;
GRANT EXECUTE ON FUNCTION alterfunction_05661_fn(integer) TO alterfunction_05661_alter;
RESET ROLE;
SET ROLE alterfunction_05661_alter;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER FUNCTION。
-- primary-target-begin
ALTER FUNCTION alterfunction_05661_fn(integer) LEAKPROOF;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT p.provolatile, p.prokind, p.prosecdef, p.proleakproof, p.proparallel, p.procost, p.prorows FROM pg_catalog.pg_proc AS p WHERE p.proname = 'alterfunction_05661_fn' ORDER BY p.proname, p.oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION alterfunction_05661_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterfunction_05661_fn(integer) CASCADE;
DROP OWNED BY alterfunction_05661_alter;
DROP ROLE IF EXISTS alterfunction_05661_alter;
DROP OWNED BY alterfunction_05661_owner;
DROP ROLE IF EXISTS alterfunction_05661_owner;
