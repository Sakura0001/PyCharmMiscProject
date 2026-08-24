-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : PREPARE TRANSACTION transaction_state=savepoint_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: PREPARETRANSACTION07844
-- source_md: skills/pg-sql-generation/references/statements/tcl/two_phase_transaction/prepare_transaction.md
-- factor_md: skills/pg-sql-generation/references/combinations/tcl/two_phase_transaction/prepare_transaction.yaml
-- primary_obligation_id: PREPARETRANSACTION-EXT|07844|error_assertion|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 25001
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS preparetransaction_07844_data;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE preparetransaction_07844_data (id integer, payload text);
INSERT INTO preparetransaction_07844_data VALUES (1, 'prepare_transaction_fixture');
BEGIN;
SAVEPOINT preparetransaction_07844_sp;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 PREPARE TRANSACTION。
-- primary-target-begin
PREPARE TRANSACTION 'preparetransaction_07844_tx';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '25001' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS preparetransaction_07844_data;
