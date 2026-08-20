-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : MERGE constraint_boundary=constraint_violation
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: MERGE05806
-- source_md: skills/pg-sql-generation/references/statements/dml/table/merge.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/merge.yaml
-- primary_obligation_id: MERGE-EXT|05806|effect_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 23000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS merge_05806_tbl, merge_05806_src, merge_05806_ref CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE merge_05806_tbl (id int PRIMARY KEY, val int);
CREATE TABLE merge_05806_ref (id int REFERENCES merge_05806_tbl(id));
INSERT INTO merge_05806_tbl VALUES (1, 100);
INSERT INTO merge_05806_ref VALUES (1);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 MERGE。
-- primary-target-begin
WITH merge_05806_cte AS (SELECT 1 AS id, 100 AS val)
MERGE INTO public.merge_05806_tbl USING merge_05806_cte AS s ON public.merge_05806_tbl.id = s.id WHEN MATCHED THEN DELETE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '23000' AS target_sqlstate_matches_expected;
SELECT count(*) >= 0 AS effect_state FROM merge_05806_tbl ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS merge_05806_tbl, merge_05806_src, merge_05806_ref CASCADE;
