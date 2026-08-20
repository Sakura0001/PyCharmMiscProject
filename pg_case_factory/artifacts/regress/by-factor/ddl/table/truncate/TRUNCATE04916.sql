-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : TRUNCATE target_action=truncate
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: TRUNCATE04916
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/truncate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/truncate.yaml
-- primary_obligation_id: TRUNCATE-EXT|04916|sequence_reset_check|restart_identity_resets_sequences
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS truncate_04916_tbl, truncate_04916_ref CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE truncate_04916_tbl (id int GENERATED ALWAYS AS IDENTITY, val int);
INSERT INTO truncate_04916_tbl (val) VALUES (100), (200);
-- 3. 执行唯一获得覆盖信用的 TRUNCATE。
-- primary-target-begin
TRUNCATE TABLE truncate_04916_tbl CONTINUE IDENTITY RESTRICT ;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS effect_state FROM truncate_04916_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS truncate_04916_tbl, truncate_04916_ref CASCADE;
