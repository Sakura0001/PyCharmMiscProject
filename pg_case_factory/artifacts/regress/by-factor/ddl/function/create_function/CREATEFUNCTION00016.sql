-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE FUNCTION argtype=enum_type
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEFUNCTION00016
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/create_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/create_function.yaml
-- primary_obligation_id: CFUNC-SFV|sfv-dce9149b779a4ba986c0819c|create_function
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS createfunction_00016_fn(createfunction_00016_etype) CASCADE;
DROP TYPE IF EXISTS createfunction_00016_ctype CASCADE;
DROP TYPE IF EXISTS createfunction_00016_etype CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createfunction_00016_etype AS ENUM ('red', 'green', 'blue');
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE FUNCTION。
-- primary-target-begin
CREATE FUNCTION createfunction_00016_fn(createfunction_00016_etype) RETURNS createfunction_00016_etype LANGUAGE sql RETURN $1;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS function_state FROM pg_catalog.pg_proc WHERE proname = 'createfunction_00016_fn' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TYPE IF EXISTS createfunction_00016_etype CASCADE;
DROP FUNCTION IF EXISTS createfunction_00016_fn(createfunction_00016_etype);
