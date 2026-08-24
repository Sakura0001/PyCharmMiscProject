-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP PROCEDURE target_procedure_not_exists=without_IF_EXISTS_error
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPPROCEDURE00077
-- source_md: skills/pg-sql-generation/references/statements/ddl/procedure/drop_procedure.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/procedure/drop_procedure.yaml
-- primary_obligation_id: DROPPROCEDURE-EXT|00077|drop_procedure|information_schema_routines|DROP_PROCEDURE_cascade
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PROCEDURE IF EXISTS "dropprocedure_00077_select"(integer) CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
SELECT 1 AS target_procedure_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP PROCEDURE。
-- primary-target-begin
DROP PROCEDURE "dropprocedure_00077_select"(integer) CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS procedure_absent FROM pg_catalog.pg_proc WHERE proname = 'dropprocedure_00077_select' AND prokind = 'p' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP PROCEDURE IF EXISTS "dropprocedure_00077_select"(integer) CASCADE;
