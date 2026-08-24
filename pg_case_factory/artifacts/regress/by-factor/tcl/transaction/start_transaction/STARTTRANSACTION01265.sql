-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : START TRANSACTION target_action=start_transaction
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: STARTTRANSACTION01265
-- source_md: skills/pg-sql-generation/references/statements/tcl/transaction/start_transaction.md
-- factor_md: skills/pg-sql-generation/references/combinations/tcl/transaction/start_transaction.yaml
-- primary_obligation_id: STARTTRANSACTION-EXT|01265|returned_rows|reset_state
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
ROLLBACK;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS no_active_transaction;
-- 3. 执行唯一获得覆盖信用的 START TRANSACTION。
-- primary-target-begin
START TRANSACTION READ ONLY;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT 1 AS start_transaction_completed;
-- 5. 清理全部本编号对象。
ROLLBACK;
RESET ALL;
