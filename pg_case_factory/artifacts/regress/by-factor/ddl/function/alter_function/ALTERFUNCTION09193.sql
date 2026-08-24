-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER FUNCTION argtype_specification=with_partial_signature
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFUNCTION09193
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/alter_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/alter_function.yaml
-- primary_obligation_id: AF-EXT|09193|security_definer|pg_get_functiondef|DROP_FUNCTION
-- expected_outcome: expected_failure
-- expected_sqlstate: 42883
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS "alterfunction_09193_Mixed Function"(integer) CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地函数和因子专用夹具。
CREATE FUNCTION "alterfunction_09193_Mixed Function"(integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE sql;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER FUNCTION。
-- primary-target-begin
ALTER FUNCTION "alterfunction_09193_Mixed Function"(integer, text) SECURITY DEFINER RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42883' AS target_sqlstate_matches_expected;
SELECT pg_get_functiondef(p.oid) FROM pg_catalog.pg_proc AS p WHERE p.proname = 'alterfunction_09193_Mixed Function' ORDER BY p.oid;
-- 5. 清理全部本编号对象。
DROP FUNCTION "alterfunction_09193_Mixed Function"(integer);
DROP FUNCTION IF EXISTS "alterfunction_09193_Mixed Function"(integer) CASCADE;
