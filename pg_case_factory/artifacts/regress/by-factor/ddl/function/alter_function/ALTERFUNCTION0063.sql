-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER FUNCTION configuration_parameter_shape=valid_parameter
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFUNCTION0063
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/alter_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/alter_function.yaml
-- primary_obligation_id: AF-SFV|sfv-836ce40cb9450f2d690e7465|set_parameter
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS alterfunction_0063_fn(integer) CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地函数和因子专用夹具。
CREATE FUNCTION alterfunction_0063_fn(integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE sql;
-- 3. 执行唯一获得覆盖信用的 ALTER FUNCTION。
-- primary-target-begin
ALTER FUNCTION alterfunction_0063_fn(integer) SET work_mem TO 100;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT p.provolatile, p.prokind, p.prosecdef, p.proleakproof, p.proparallel, p.procost, p.prorows FROM pg_catalog.pg_proc AS p WHERE p.proname = 'alterfunction_0063_fn' ORDER BY p.proname, p.oid;
-- 5. 清理全部本编号对象。
DROP FUNCTION IF EXISTS alterfunction_0063_fn(integer);
DROP FUNCTION IF EXISTS alterfunction_0063_fn(integer) CASCADE;
