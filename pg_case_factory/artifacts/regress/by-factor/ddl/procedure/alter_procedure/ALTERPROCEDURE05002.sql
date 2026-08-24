-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER PROCEDURE rename_target=duplicate_name
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPROCEDURE05002
-- source_md: skills/pg-sql-generation/references/statements/ddl/procedure/alter_procedure.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/procedure/alter_procedure.yaml
-- primary_obligation_id: AP-EXT|05002|rename|pg_proc_catalog_query|DROP_PROCEDURE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42723
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PROCEDURE IF EXISTS "alterprocedure_05002_select"(integer) CASCADE;
DROP PROCEDURE IF EXISTS alterprocedure_05002_dup_proc(integer) CASCADE;
DROP PROCEDURE IF EXISTS alterprocedure_05002_dup_proc(integer) CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE PROCEDURE "alterprocedure_05002_select"(integer) LANGUAGE sql AS $$ SELECT 1 $$;
CREATE PROCEDURE alterprocedure_05002_dup_proc(integer) LANGUAGE sql AS $$ SELECT 1 $$;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER PROCEDURE。
-- primary-target-begin
ALTER PROCEDURE "alterprocedure_05002_select"(integer) RENAME TO alterprocedure_05002_dup_proc;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42723' AS target_sqlstate_matches_expected;
SELECT p.prokind, p.prosecdef FROM pg_catalog.pg_proc AS p WHERE p.proname = 'alterprocedure_05002_select' ORDER BY p.proname, p.oid;
-- 5. 清理全部本编号对象。
DROP PROCEDURE "alterprocedure_05002_select"(integer) CASCADE;
DROP PROCEDURE IF EXISTS "alterprocedure_05002_select"(integer) CASCADE;
DROP PROCEDURE IF EXISTS alterprocedure_05002_dup_proc(integer) CASCADE;
DROP PROCEDURE IF EXISTS alterprocedure_05002_dup_proc(integer) CASCADE;
