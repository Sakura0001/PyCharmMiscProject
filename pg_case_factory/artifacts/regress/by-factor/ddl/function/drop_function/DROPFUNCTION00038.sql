-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP FUNCTION target_function_different_type=same_name_is_aggregate
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPFUNCTION00038
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/drop_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/drop_function.yaml
-- primary_obligation_id: DROPFUNCTION-SFV|sfv-781336da7515f4ed65f90615|drop_function
-- expected_outcome: expected_failure
-- expected_sqlstate: 42809
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE IF EXISTS dropfunction_00038_fn(integer);
\set ON_ERROR_STOP on
-- 2. 创建完整本地函数和因子专用夹具。
CREATE AGGREGATE dropfunction_00038_fn(integer) (SFUNC = int4_inc, INITCOND = '0', STYPE = bigint);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP FUNCTION。
-- primary-target-begin
DROP FUNCTION dropfunction_00038_fn;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42809' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS function_present FROM pg_catalog.pg_proc WHERE proname = 'dropfunction_00038_fn' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP AGGREGATE IF EXISTS dropfunction_00038_fn(integer);
