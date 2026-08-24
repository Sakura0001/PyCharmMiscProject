-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE PROCEDURE target_form=create_procedure
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEPROCEDURE02700
-- source_md: skills/pg-sql-generation/references/statements/ddl/procedure/create_procedure.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/procedure/create_procedure.yaml
-- primary_obligation_id: CPROC-EXT|02700|branch_1|information_schema_routines|DROP_PROCEDURE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PROCEDURE IF EXISTS createprocedure_02700_proc(integer) CASCADE;
DROP FUNCTION IF EXISTS createprocedure_02700_proc(integer) CASCADE;
DROP TYPE IF EXISTS createprocedure_02700_ctype CASCADE;
DROP TYPE IF EXISTS createprocedure_02700_etype CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE PROCEDURE。
-- primary-target-begin
CREATE PROCEDURE createprocedure_02700_proc(integer) LANGUAGE plpgsql SECURITY INVOKER TRANSFORM FOR TYPE text AS 'BEGIN\n  NULL;\nEND;';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS procedure_state FROM information_schema.routines WHERE routine_name = 'createprocedure_02700_proc' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP PROCEDURE createprocedure_02700_proc(integer);
