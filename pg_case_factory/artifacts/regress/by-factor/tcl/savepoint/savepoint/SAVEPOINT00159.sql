-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SAVEPOINT transaction_state=outside_transaction
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SAVEPOINT00159
-- source_md: skills/pg-sql-generation/references/statements/tcl/savepoint/savepoint.md
-- factor_md: skills/pg-sql-generation/references/combinations/tcl/savepoint/savepoint.yaml
-- primary_obligation_id: SAVEPOINT-EXT|00159|returned_rows|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 25P01
-- 1. 清理本编号对象，保证脚本可重复执行。
ROLLBACK;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS no_active_transaction;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 SAVEPOINT。
-- primary-target-begin
SAVEPOINT savepoint_00159_sp AND CHAIN;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '25P01' AS target_sqlstate_matches_expected;
SELECT 1 AS savepoint_completed;
-- 5. 清理全部本编号对象。
ROLLBACK;
