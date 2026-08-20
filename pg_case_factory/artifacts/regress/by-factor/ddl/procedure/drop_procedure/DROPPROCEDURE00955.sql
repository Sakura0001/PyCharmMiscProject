-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP PROCEDURE dependent_objects=has_dependents_cascade_removes
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPPROCEDURE00955
-- source_md: skills/pg-sql-generation/references/statements/ddl/procedure/drop_procedure.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/procedure/drop_procedure.yaml
-- primary_obligation_id: DROPPROCEDURE-EXT|00955|drop_procedure|information_schema_routines|no_cleanup_needed
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PROCEDURE IF EXISTS "dropprocedure_00955_select"(integer) CASCADE;
DROP FUNCTION IF EXISTS dropprocedure_00955_dep;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE PROCEDURE "dropprocedure_00955_select"(integer) AS $$ BEGIN END; $$ LANGUAGE plpgsql;
CREATE FUNCTION dropprocedure_00955_dep() RETURNS void AS $$ BEGIN CALL "dropprocedure_00955_select"(0); END; $$ LANGUAGE plpgsql;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP PROCEDURE。
-- primary-target-begin
DROP PROCEDURE IF EXISTS "dropprocedure_00955_select"(integer) RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS procedure_present FROM pg_catalog.pg_proc WHERE proname = 'dropprocedure_00955_select' AND prokind = 'p' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP PROCEDURE IF EXISTS "dropprocedure_00955_select"(integer) CASCADE;
DROP FUNCTION IF EXISTS dropprocedure_00955_dep;
