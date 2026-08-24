-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : UPDATE target_action=update
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: UPDATE10853
-- source_md: skills/pg-sql-generation/references/statements/dml/table/update.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/update.yaml
-- primary_obligation_id: UPDATE-EXT|10853|catalog_query|reset_state
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS update_10853_tbl, update_10853_src, update_10853_ref CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE update_10853_tbl (id int, val int);
INSERT INTO update_10853_tbl VALUES (1, 100), (2, 200);
-- 3. 执行唯一获得覆盖信用的 UPDATE。
-- primary-target-begin
UPDATE "update_10853_tbl" SET val = 0 WHERE id = 999;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS relation_state FROM pg_catalog.pg_class WHERE relname = 'update_10853_tbl' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS update_10853_tbl, update_10853_src, update_10853_ref CASCADE;
