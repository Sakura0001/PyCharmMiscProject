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
-- case_id: ALTERFUNCTION04336
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/alter_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/alter_function.yaml
-- primary_obligation_id: AF-EXT|04336|depends_on_extension|pg_proc_catalog_query|DROP_FUNCTION
-- expected_outcome: expected_failure
-- expected_sqlstate: 42883
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS alterfunction_04336_src_schema.alterfunction_04336_fn(integer) CASCADE;
DROP ROLE IF EXISTS alterfunction_04336_owner;
DROP SCHEMA IF EXISTS alterfunction_04336_src_schema CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地函数和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS alterfunction_04336_src_schema;
CREATE ROLE alterfunction_04336_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterfunction_04336_owner;
GRANT CREATE ON SCHEMA alterfunction_04336_src_schema TO alterfunction_04336_owner;
GRANT USAGE ON SCHEMA alterfunction_04336_src_schema TO alterfunction_04336_owner;
SET ROLE alterfunction_04336_owner;
CREATE FUNCTION alterfunction_04336_src_schema.alterfunction_04336_fn(integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE sql;
RESET ROLE;
SET ROLE alterfunction_04336_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER FUNCTION。
-- primary-target-begin
ALTER FUNCTION alterfunction_04336_src_schema.alterfunction_04336_fn(integer, text) DEPENDS ON EXTENSION plpgsql;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42883' AS target_sqlstate_matches_expected;
SELECT p.provolatile, p.prokind, p.prosecdef, p.proleakproof, p.proparallel, p.procost, p.prorows FROM pg_catalog.pg_proc AS p WHERE p.proname = 'alterfunction_04336_fn' ORDER BY p.proname, p.oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION alterfunction_04336_src_schema.alterfunction_04336_fn(integer);
DROP FUNCTION IF EXISTS alterfunction_04336_src_schema.alterfunction_04336_fn(integer) CASCADE;
DROP OWNED BY alterfunction_04336_owner;
DROP ROLE IF EXISTS alterfunction_04336_owner;
DROP SCHEMA IF EXISTS alterfunction_04336_src_schema CASCADE;
