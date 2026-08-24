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
-- case_id: CHECKPOINT08633
-- source_md: skills/pg-sql-generation/references/statements/utility/checkpoint/checkpoint.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/checkpoint/checkpoint.yaml
-- primary_obligation_id: CP-EXT|08633|returned_rows|rollback
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS checkpoint_08633_data;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE checkpoint_08633_data (id integer, payload text);
INSERT INTO checkpoint_08633_data VALUES (1, 'checkpoint_fixture');
-- 3. 执行唯一获得覆盖信用的 CHECKPOINT。
-- primary-target-begin
CHECKPOINT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS row_count FROM checkpoint_08633_data ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS checkpoint_08633_data;
