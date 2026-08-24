-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER PROCEDURE configuration_parameter_shape=invalid_parameter
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPROCEDURE09928
-- source_md: skills/pg-sql-generation/references/statements/ddl/procedure/alter_procedure.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/procedure/alter_procedure.yaml
-- primary_obligation_id: AP-EXT|09928|reset_parameter|information_schema_routines|DROP_PROCEDURE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PROCEDURE IF EXISTS "alterprocedure_09928_Mixed Procedure"(integer) CASCADE;
DROP ROLE IF EXISTS alterprocedure_09928_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE ROLE alterprocedure_09928_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterprocedure_09928_owner;
SET ROLE alterprocedure_09928_owner;
CREATE PROCEDURE "alterprocedure_09928_Mixed Procedure"(integer) LANGUAGE sql AS $$ SELECT 1 $$;
RESET ROLE;
SET ROLE alterprocedure_09928_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER PROCEDURE。
-- primary-target-begin
ALTER PROCEDURE "alterprocedure_09928_Mixed Procedure" RESET alterprocedure_09928_no_such_guc RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT r.routine_schema, r.routine_name, r.routine_type FROM information_schema.routines AS r WHERE r.routine_name = 'alterprocedure_09928_Mixed Procedure' ORDER BY r.routine_schema, r.routine_name;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PROCEDURE "alterprocedure_09928_Mixed Procedure"(integer) CASCADE;
DROP PROCEDURE IF EXISTS "alterprocedure_09928_Mixed Procedure"(integer) CASCADE;
DROP OWNED BY alterprocedure_09928_owner;
DROP ROLE IF EXISTS alterprocedure_09928_owner;
