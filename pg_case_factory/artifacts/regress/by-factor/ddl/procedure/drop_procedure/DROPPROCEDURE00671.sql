-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP PROCEDURE privilege_level=non_owner_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPPROCEDURE00671
-- source_md: skills/pg-sql-generation/references/statements/ddl/procedure/drop_procedure.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/procedure/drop_procedure.yaml
-- primary_obligation_id: DROPPROCEDURE-EXT|00671|drop_procedure|information_schema_routines|DROP_PROCEDURE_cascade
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PROCEDURE IF EXISTS dropprocedure_00671_schema.dropprocedure_00671_proc(integer) CASCADE;
DROP SCHEMA IF EXISTS dropprocedure_00671_schema CASCADE;
DROP OWNED BY dropprocedure_00671_actor;
DROP ROLE IF EXISTS dropprocedure_00671_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE ROLE dropprocedure_00671_actor LOGIN NOSUPERUSER;
CREATE SCHEMA dropprocedure_00671_schema;
CREATE PROCEDURE dropprocedure_00671_schema.dropprocedure_00671_proc(integer) AS $$ BEGIN END; $$ LANGUAGE plpgsql;
SET ROLE dropprocedure_00671_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP PROCEDURE。
-- primary-target-begin
DROP PROCEDURE IF EXISTS dropprocedure_00671_schema.dropprocedure_00671_proc(integer) CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS procedure_present FROM pg_catalog.pg_proc WHERE proname = 'dropprocedure_00671_proc' AND prokind = 'p' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PROCEDURE IF EXISTS dropprocedure_00671_schema.dropprocedure_00671_proc(integer) CASCADE;
DROP SCHEMA IF EXISTS dropprocedure_00671_schema CASCADE;
DROP OWNED BY dropprocedure_00671_actor;
DROP ROLE IF EXISTS dropprocedure_00671_actor;
