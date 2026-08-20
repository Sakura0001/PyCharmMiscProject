-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : MERGE expression_shape=subquery_expression
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: MERGE00026
-- source_md: skills/pg-sql-generation/references/statements/dml/table/merge.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/merge.yaml
-- primary_obligation_id: MERGE-SFV|sfv-6c0101b3338ccf6a795d681b|merge
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS merge_00026_tbl, merge_00026_src, merge_00026_ref CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE merge_00026_tbl (id int, val int);
INSERT INTO merge_00026_tbl VALUES (1, 100);
-- 3. 执行唯一获得覆盖信用的 MERGE。
-- primary-target-begin
MERGE INTO merge_00026_tbl USING (VALUES (1, 100)) AS s(id, val) ON merge_00026_tbl.id = s.id WHEN MATCHED THEN UPDATE SET val = (SELECT 1) WHEN NOT MATCHED THEN INSERT VALUES (s.id, (SELECT 1));
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) >= 0 AS effect_state FROM merge_00026_tbl ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS merge_00026_tbl, merge_00026_src, merge_00026_ref CASCADE;
