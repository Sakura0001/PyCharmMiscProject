-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SELECT INTO duplicate_table_name=without_if_not_exists_error
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SELECTINTO00007
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/select_into.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/select_into.yaml
-- primary_obligation_id: SELECTINTO-SFV|sfv-03c5fb37c131ec9c9ea25f5f|select_into
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P07
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS selectinto_00007_src, selectinto_00007_t CASCADE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE selectinto_00007_src (id integer, val text);
INSERT INTO selectinto_00007_src VALUES (1, 'a'), (2, 'b');
CREATE TABLE selectinto_00007_t (id integer, val text);
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 SELECT INTO。
-- primary-target-begin
SELECT * INTO selectinto_00007_t FROM selectinto_00007_src;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P07' AS target_sqlstate_matches_expected;
SELECT count(*) AS target_created_count FROM pg_catalog.pg_class c WHERE c.relname = 'selectinto_00007_t' AND c.relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS selectinto_00007_src, selectinto_00007_t CASCADE;
