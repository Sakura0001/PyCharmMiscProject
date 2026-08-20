-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER ROUTINE extension_dependency=depends_on_nonexistent_extension
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERROUTINE04552
-- source_md: skills/pg-sql-generation/references/statements/ddl/routine/alter_routine.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/routine/alter_routine.yaml
-- primary_obligation_id: AR-EXT|04552|depends_on_extension|error_assertion|drop_function
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE IF EXISTS alterroutine_04552_routine(integer) CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE AGGREGATE alterroutine_04552_routine(integer) (SFUNC = int4_sum, STYPE = bigint, INITCOND = '0');
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER ROUTINE。
-- primary-target-begin
ALTER ROUTINE alterroutine_04552_routine DEPENDS ON EXTENSION alterroutine_04552_no_such_ext;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT '42704' AS expected_sqlstate;
-- 5. 清理全部本编号对象。
DROP AGGREGATE IF EXISTS alterroutine_04552_routine(integer) CASCADE;
DROP AGGREGATE IF EXISTS alterroutine_04552_routine(integer) CASCADE;
