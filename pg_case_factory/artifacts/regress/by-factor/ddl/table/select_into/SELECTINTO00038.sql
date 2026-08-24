-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SELECT INTO source_table_dependency=source_table_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SELECTINTO00038
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/select_into.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/select_into.yaml
-- primary_obligation_id: SELECTINTO-SFV|sfv-3e1261a57ecced64d66ab55e|select_into
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS selectinto_00038_t CASCADE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地表和因子专用夹具。
SELECT 1 AS target_table_intentionally_absent;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 SELECT INTO。
-- primary-target-begin
SELECT * INTO selectinto_00038_t FROM selectinto_00038_src;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS table_count FROM pg_catalog.pg_class c WHERE c.relname = 'selectinto_00038_t' AND c.relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS selectinto_00038_t CASCADE;
