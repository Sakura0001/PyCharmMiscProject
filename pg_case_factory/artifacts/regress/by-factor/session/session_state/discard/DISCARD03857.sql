-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DISCARD transaction_visibility=inside_rolled_back_transaction
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DISCARD03857
-- source_md: skills/pg-sql-generation/references/statements/session/session_state/discard.md
-- factor_md: skills/pg-sql-generation/references/combinations/session/session_state/discard.yaml
-- primary_obligation_id: DIS-EXT|03857|error_assertion|reset_state|invalid_transaction
-- expected_outcome: expected_failure
-- expected_sqlstate: 25001
-- 1. 清理本编号对象，保证脚本可重复执行。
ROLLBACK;
RESET ROLE;
RESET work_mem;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
SET work_mem = '64MB';
BEGIN;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DISCARD。
-- primary-target-begin
DISCARD ALL;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
ROLLBACK;
SELECT :'target_sqlstate' = '25001' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
ROLLBACK;
RESET work_mem;
