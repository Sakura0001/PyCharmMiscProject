-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SELECT INTO reserved_schema_name=pg_catalog
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SELECTINTO00029
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/select_into.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/select_into.yaml
-- primary_obligation_id: SELECTINTO-SFV|sfv-ab42f041ebb427036ab51c11|select_into
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS selectinto_00029_src, selectinto_00029_sch.selectinto_00029_t CASCADE;
DROP SCHEMA IF EXISTS selectinto_00029_sch CASCADE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS selectinto_00029_sch;
CREATE TABLE selectinto_00029_src (id integer, val text);
INSERT INTO selectinto_00029_src VALUES (1, 'a'), (2, 'b');
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 SELECT INTO。
-- primary-target-begin
SELECT * INTO selectinto_00029_sch.selectinto_00029_t FROM selectinto_00029_src;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS target_created_count FROM pg_catalog.pg_class c WHERE c.relname = 'selectinto_00029_t' AND c.relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS selectinto_00029_sch CASCADE;
DROP TABLE IF EXISTS selectinto_00029_src, selectinto_00029_sch.selectinto_00029_t CASCADE;
