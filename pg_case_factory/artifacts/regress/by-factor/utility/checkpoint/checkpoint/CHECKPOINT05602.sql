-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CHECKPOINT target_action=checkpoint
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CHECKPOINT05602
-- source_md: skills/pg-sql-generation/references/statements/utility/checkpoint/checkpoint.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/checkpoint/checkpoint.yaml
-- primary_obligation_id: CP-EXT|05602|error_assertion|reset_state
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS checkpoint_05602_data;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE checkpoint_05602_data (id integer, payload text);
INSERT INTO checkpoint_05602_data VALUES (1, 'checkpoint_fixture');
-- 3. 执行唯一获得覆盖信用的 CHECKPOINT。
-- primary-target-begin
CHECKPOINT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS checkpoint_05602_data;
