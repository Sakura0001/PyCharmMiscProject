-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : PREPARE TRANSACTION target_action=prepare_transaction
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: PREPARETRANSACTION06904
-- source_md: skills/pg-sql-generation/references/statements/tcl/two_phase_transaction/prepare_transaction.md
-- factor_md: skills/pg-sql-generation/references/combinations/tcl/two_phase_transaction/prepare_transaction.yaml
-- primary_obligation_id: PREPARETRANSACTION-EXT|06904|returned_rows|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS preparetransaction_06904_data;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE preparetransaction_06904_data (id integer, payload text);
INSERT INTO preparetransaction_06904_data VALUES (1, 'prepare_transaction_fixture');
BEGIN;
INSERT INTO preparetransaction_06904_data VALUES (2, 'prepared_row');
-- 3. 执行唯一获得覆盖信用的 PREPARE TRANSACTION。
-- primary-target-begin
PREPARE TRANSACTION 'preparetransaction_06904_duptx';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT id, payload FROM preparetransaction_06904_data ORDER BY id;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS preparetransaction_06904_data;
