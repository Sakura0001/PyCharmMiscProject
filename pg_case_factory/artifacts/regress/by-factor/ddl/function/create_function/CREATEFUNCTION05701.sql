-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE FUNCTION target_form=create_function
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEFUNCTION05701
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/create_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/create_function.yaml
-- primary_obligation_id: CFUNC-EXT|05701|branch_2|pg_get_functiondef|DROP_FUNCTION_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS createfunction_05701_fn(integer) CASCADE;
DROP TYPE IF EXISTS createfunction_05701_ctype CASCADE;
DROP TYPE IF EXISTS createfunction_05701_etype CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE FUNCTION。
-- primary-target-begin
CREATE OR REPLACE FUNCTION createfunction_05701_fn(integer) RETURNS TABLE (col integer) LANGUAGE plpython3u IMMUTABLE PARALLEL UNSAFE AS 'no_such_body';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT pg_get_functiondef('createfunction_05701_fn(integer)'::regprocedure) AS function_def;
-- 5. 清理全部本编号对象。
DROP FUNCTION createfunction_05701_fn(integer) CASCADE;
