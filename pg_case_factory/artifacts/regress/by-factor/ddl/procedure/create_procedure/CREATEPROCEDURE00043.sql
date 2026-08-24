-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE PROCEDURE expected_status=failure
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEPROCEDURE00043
-- source_md: skills/pg-sql-generation/references/statements/ddl/procedure/create_procedure.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/procedure/create_procedure.yaml
-- primary_obligation_id: CPROC-SFV|sfv-216ea10aa109b3c2f3f9bca7|create_procedure
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PROCEDURE IF EXISTS createprocedure_00043_proc(integer) CASCADE;
DROP FUNCTION IF EXISTS createprocedure_00043_proc(integer) CASCADE;
DROP TYPE IF EXISTS createprocedure_00043_ctype CASCADE;
DROP TYPE IF EXISTS createprocedure_00043_etype CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE PROCEDURE createprocedure_00043_proc(integer) LANGUAGE sql AS 'NULL';
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE PROCEDURE。
-- primary-target-begin
CREATE PROCEDURE createprocedure_00043_proc(integer) LANGUAGE sql BEGIN ATOMIC NULL; END;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS procedure_state FROM pg_catalog.pg_proc WHERE proname = 'createprocedure_00043_proc' AND prokind = 'p' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP PROCEDURE IF EXISTS createprocedure_00043_proc(integer);
