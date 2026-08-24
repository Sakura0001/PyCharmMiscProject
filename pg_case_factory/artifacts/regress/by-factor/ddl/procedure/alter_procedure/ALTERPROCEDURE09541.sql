-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER PROCEDURE argtype_specification=with_partial_signature
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPROCEDURE09541
-- source_md: skills/pg-sql-generation/references/statements/ddl/procedure/alter_procedure.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/procedure/alter_procedure.yaml
-- primary_obligation_id: AP-EXT|09541|reset_parameter|information_schema_routines|DROP_PROCEDURE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42883
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PROCEDURE IF EXISTS "alterprocedure_09541_Mixed Procedure"(integer) CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE PROCEDURE "alterprocedure_09541_Mixed Procedure"(integer) LANGUAGE sql AS $$ SELECT 1 $$;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER PROCEDURE。
-- primary-target-begin
ALTER PROCEDURE "alterprocedure_09541_Mixed Procedure"(integer, text) RESET work_mem;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42883' AS target_sqlstate_matches_expected;
SELECT r.routine_schema, r.routine_name, r.routine_type FROM information_schema.routines AS r WHERE r.routine_name = 'alterprocedure_09541_Mixed Procedure' ORDER BY r.routine_schema, r.routine_name;
-- 5. 清理全部本编号对象。
DROP PROCEDURE "alterprocedure_09541_Mixed Procedure"(integer) CASCADE;
DROP PROCEDURE IF EXISTS "alterprocedure_09541_Mixed Procedure"(integer) CASCADE;
