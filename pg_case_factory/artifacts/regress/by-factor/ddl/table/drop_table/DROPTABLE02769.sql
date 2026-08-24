-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TABLE dependency_state=has_fk_references
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTABLE02769
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/drop_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/drop_table.yaml
-- primary_obligation_id: DROPTABLE-EXT|02769|drop_table|notice_assertion|cascade_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droptable_02769_t CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE TABLE droptable_02769_t (c integer);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TABLE。
-- primary-target-begin
DROP TABLE IF EXISTS droptable_02769_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS table_present FROM pg_catalog.pg_class WHERE relname = 'droptable_02769_t' AND relkind = 'r' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS droptable_02769_t CASCADE;
