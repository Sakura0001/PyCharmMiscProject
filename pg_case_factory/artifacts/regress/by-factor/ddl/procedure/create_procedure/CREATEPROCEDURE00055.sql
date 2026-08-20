-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE PROCEDURE language_not_available=untrusted_language_requires_superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEPROCEDURE00055
-- source_md: skills/pg-sql-generation/references/statements/ddl/procedure/create_procedure.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/procedure/create_procedure.yaml
-- primary_obligation_id: CPROC-SFV|sfv-37dfee40652f5cee4163835d|create_procedure
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PROCEDURE IF EXISTS createprocedure_00055_proc(integer) CASCADE;
DROP FUNCTION IF EXISTS createprocedure_00055_proc(integer) CASCADE;
DROP TYPE IF EXISTS createprocedure_00055_ctype CASCADE;
DROP TYPE IF EXISTS createprocedure_00055_etype CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createprocedure_00055_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createprocedure_00055_actor LOGIN NOSUPERUSER;
SET ROLE createprocedure_00055_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE PROCEDURE。
-- primary-target-begin
CREATE PROCEDURE createprocedure_00055_proc(integer) LANGUAGE c AS '$libdir/no_such_file', 'no_such_symbol';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS procedure_state FROM pg_catalog.pg_proc WHERE proname = 'createprocedure_00055_proc' AND prokind = 'p' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PROCEDURE IF EXISTS createprocedure_00055_proc(integer);
DROP OWNED BY createprocedure_00055_actor CASCADE;
DROP ROLE IF EXISTS createprocedure_00055_actor;
