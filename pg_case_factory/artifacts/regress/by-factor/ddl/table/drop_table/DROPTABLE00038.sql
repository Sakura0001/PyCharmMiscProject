-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TABLE table_name_shape=quoted
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTABLE00038
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/drop_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/drop_table.yaml
-- primary_obligation_id: DROPTABLE-SFV|sfv-beb579fa85726a3f893216ca|drop_table
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droptable_00038_qt CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE TABLE droptable_00038_qt (c integer);
-- 3. 执行唯一获得覆盖信用的 DROP TABLE。
-- primary-target-begin
DROP TABLE "droptable_00038_qt";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS table_absent FROM pg_catalog.pg_class WHERE relname = 'droptable_00038_qt' AND relkind = 'r' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS droptable_00038_qt CASCADE;
