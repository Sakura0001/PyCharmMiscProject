-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : EXECUTE invalid_combination=syntax_valid_semantic_error
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: EXECUTE07519
-- source_md: skills/pg-sql-generation/references/statements/prepared/prepared_statement/execute.md
-- factor_md: skills/pg-sql-generation/references/combinations/prepared/prepared_statement/execute.yaml
-- primary_obligation_id: EXECUTE-EXT|07519|catalog_query|rollback|boundary_cross
-- expected_outcome: expected_failure
-- expected_sqlstate: 42601
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS execute_07519_bt CASCADE;
DEALLOCATE ALL;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE execute_07519_bt (c1 int, c2 text);
INSERT INTO execute_07519_bt VALUES (1, 'hello');
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 EXECUTE。
-- primary-target-begin
EXECUTE execute_07519_nonexistent;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42601' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS prepared_present FROM pg_catalog.pg_prepared_statements WHERE name = 'execute_07519_stmt' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS execute_07519_bt CASCADE;
DROP TABLE IF EXISTS execute_07519_bt CASCADE;
