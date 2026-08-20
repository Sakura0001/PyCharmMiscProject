-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : MERGE target_action=merge
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: MERGE13591
-- source_md: skills/pg-sql-generation/references/statements/dml/table/merge.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/merge.yaml
-- primary_obligation_id: MERGE-EXT|13591|catalog_query|reset_state
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS merge_13591_tbl, merge_13591_src, merge_13591_ref CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE merge_13591_tbl (id int, val int);
INSERT INTO merge_13591_tbl VALUES (1, 100);
-- 3. 执行唯一获得覆盖信用的 MERGE。
-- primary-target-begin
WITH merge_13591_cte AS (SELECT 1 AS id, 100 AS val)
MERGE INTO merge_13591_tbl AS t USING merge_13591_cte AS s ON t.id = s.id WHEN MATCHED THEN UPDATE SET val = (SELECT 1) WHEN NOT MATCHED THEN INSERT VALUES (s.id, (SELECT 1));
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS relation_state FROM pg_catalog.pg_class WHERE relname = 'merge_13591_tbl' AND relkind = 'r' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS merge_13591_tbl, merge_13591_src, merge_13591_ref CASCADE;
