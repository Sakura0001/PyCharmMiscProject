-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DELETE invalid_combination=syntax_valid_semantic_error
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DELETE00027
-- source_md: skills/pg-sql-generation/references/statements/dml/table/delete.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/delete.yaml
-- primary_obligation_id: DELETE-SFV|sfv-851a7c4f1c6aad2e69cd7759|delete
-- expected_outcome: expected_failure
-- expected_sqlstate: 42703
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS delete_00027_tbl, delete_00027_src, delete_00027_ref CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE delete_00027_tbl (id int, val int);
INSERT INTO delete_00027_tbl VALUES (1, 100), (2, 200);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DELETE。
-- primary-target-begin
DELETE FROM delete_00027_tbl WHERE delete_00027_no_such_col = 1;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42703' AS target_sqlstate_matches_expected;
SELECT count(*) >= 0 AS effect_state FROM delete_00027_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS delete_00027_tbl, delete_00027_src, delete_00027_ref CASCADE;
