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
-- case_id: MERGE06962
-- source_md: skills/pg-sql-generation/references/statements/dml/table/merge.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/merge.yaml
-- primary_obligation_id: MERGE-EXT|06962|error_assertion|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 23000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS merge_06962_tbl, merge_06962_src, merge_06962_ref CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE merge_06962_tbl (id int PRIMARY KEY, val int);
CREATE TABLE merge_06962_ref (id int REFERENCES merge_06962_tbl(id));
INSERT INTO merge_06962_tbl VALUES (1, 100);
INSERT INTO merge_06962_ref VALUES (1);
CREATE TABLE merge_06962_src (id int, val int);
INSERT INTO merge_06962_src VALUES (1, 100);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 MERGE。
-- primary-target-begin
MERGE INTO public.merge_06962_tbl USING merge_06962_src AS s ON public.merge_06962_tbl.id = s.id WHEN MATCHED THEN DELETE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '23000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS merge_06962_tbl, merge_06962_src, merge_06962_ref CASCADE;
