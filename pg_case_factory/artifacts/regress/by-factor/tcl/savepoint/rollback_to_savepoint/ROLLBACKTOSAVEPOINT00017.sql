-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : ROLLBACK TO SAVEPOINT invalid_combination=object_type_mismatch
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ROLLBACKTOSAVEPOINT00017
-- source_md: skills/pg-sql-generation/references/statements/tcl/savepoint/rollback_to_savepoint.md
-- factor_md: skills/pg-sql-generation/references/combinations/tcl/savepoint/rollback_to_savepoint.yaml
-- primary_obligation_id: ROLLBACKTOSAVEPOINT-SFV|sfv-4f092f92eaa6155412b1db78|rollback_to_savepoint
-- expected_outcome: expected_failure
-- expected_sqlstate: 42809
-- 1. 清理本编号对象，保证脚本可重复执行。
ROLLBACK;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
BEGIN;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ROLLBACK TO SAVEPOINT。
-- primary-target-begin
ROLLBACK TO SAVEPOINT rollbacktosavepoint_00017_sp;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42809' AS target_sqlstate_matches_expected;
SELECT count(*) AS session_active FROM pg_catalog.pg_stat_activity WHERE pid = pg_backend_pid() ORDER BY count(*);
-- 5. 清理全部本编号对象。
ROLLBACK;
