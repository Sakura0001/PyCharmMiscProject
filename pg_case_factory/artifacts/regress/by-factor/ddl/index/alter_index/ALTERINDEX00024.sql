-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER INDEX invalid_combination=statistics_column_out_of_range
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERINDEX00024
-- source_md: skills/pg-sql-generation/references/statements/ddl/index/alter_index.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/index/alter_index.yaml
-- primary_obligation_id: AI-SFV|sfv-eee7d37e38f362e778d2b217|set_statistics
-- expected_outcome: expected_failure
-- expected_sqlstate: 42703
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterindex_00024_t CASCADE;
DROP INDEX IF EXISTS alterindex_00024_idx CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地索引和因子专用夹具。
CREATE TABLE alterindex_00024_t (id integer, tsv tsvector, pt point, rng int4range);
CREATE INDEX alterindex_00024_idx ON alterindex_00024_t USING btree ((id+1));
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER INDEX。
-- primary-target-begin
ALTER INDEX alterindex_00024_idx ALTER COLUMN 2 SET STATISTICS 1000;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42703' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS statistics_target_visible FROM pg_catalog.pg_class AS c WHERE c.relname = 'alterindex_00024_idx' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP INDEX IF EXISTS alterindex_00024_idx CASCADE;
DROP TABLE IF EXISTS alterindex_00024_t CASCADE;
