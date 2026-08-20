-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DELETE target_relation_state=missing
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DELETE11198
-- source_md: skills/pg-sql-generation/references/statements/dml/table/delete.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/delete.yaml
-- primary_obligation_id: DELETE-EXT|11198|error_assertion|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS delete_11198_tbl, delete_11198_src, delete_11198_ref CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS target_relation_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DELETE。
-- primary-target-begin
DELETE FROM delete_11198_tbl AS d WHERE id = 999;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P01' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS delete_11198_tbl, delete_11198_src, delete_11198_ref CASCADE;
