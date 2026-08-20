-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : MERGE target_relation_state=wrong_object_type
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: MERGE11644
-- source_md: skills/pg-sql-generation/references/statements/dml/table/merge.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/merge.yaml
-- primary_obligation_id: MERGE-EXT|11644|error_assertion|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42809
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS merge_11644_tbl, merge_11644_src, merge_11644_ref CASCADE;
DROP SEQUENCE IF EXISTS merge_11644_seq;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SEQUENCE merge_11644_seq;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 MERGE。
-- primary-target-begin
MERGE INTO "merge_11644_seq" USING (VALUES (1, 100)) AS s(id, val) ON merge_11644_seq.id = s.id WHEN MATCHED THEN UPDATE SET val = abs(1) WHEN NOT MATCHED THEN INSERT VALUES (s.id, abs(1));
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42809' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP SEQUENCE IF EXISTS merge_11644_seq;
DROP TABLE IF EXISTS merge_11644_tbl, merge_11644_src, merge_11644_ref CASCADE;
