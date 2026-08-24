-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER PROCEDURE object_state=not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPROCEDURE03069
-- source_md: skills/pg-sql-generation/references/statements/ddl/procedure/alter_procedure.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/procedure/alter_procedure.yaml
-- primary_obligation_id: AP-EXT|03069|depends_on_extension|information_schema_routines|DROP_PROCEDURE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42883
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS alterprocedure_03069_owner;
DROP SCHEMA IF EXISTS alterprocedure_03069_src_schema CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS alterprocedure_03069_src_schema;
CREATE ROLE alterprocedure_03069_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterprocedure_03069_owner;
GRANT CREATE ON SCHEMA alterprocedure_03069_src_schema TO alterprocedure_03069_owner;
GRANT USAGE ON SCHEMA alterprocedure_03069_src_schema TO alterprocedure_03069_owner;
SET ROLE alterprocedure_03069_owner;
SELECT 1 AS target_routine_intentionally_absent;
RESET ROLE;
SET ROLE alterprocedure_03069_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER PROCEDURE。
-- primary-target-begin
ALTER PROCEDURE alterprocedure_03069_src_schema.alterprocedure_03069_proc(integer) DEPENDS ON EXTENSION plpgsql;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42883' AS target_sqlstate_matches_expected;
SELECT r.routine_schema, r.routine_name, r.routine_type FROM information_schema.routines AS r WHERE r.routine_name = 'alterprocedure_03069_proc' ORDER BY r.routine_schema, r.routine_name;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY alterprocedure_03069_owner;
DROP ROLE IF EXISTS alterprocedure_03069_owner;
DROP SCHEMA IF EXISTS alterprocedure_03069_src_schema CASCADE;
