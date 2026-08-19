-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER INDEX column_number_value=zero
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERINDEX00008
-- source_md: skills/pg-sql-generation/references/statements/ddl/index/alter_index.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/index/alter_index.yaml
-- primary_obligation_id: AI-SFV|sfv-e8c29b86b4014081c163d8d0|set_statistics
-- expected_outcome: expected_failure
-- expected_sqlstate: 22023
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterindex_00008_t CASCADE;
DROP INDEX IF EXISTS alterindex_00008_idx CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地索引和因子专用夹具。
CREATE TABLE alterindex_00008_t (id integer, tsv tsvector, pt point, rng int4range);
CREATE INDEX alterindex_00008_idx ON alterindex_00008_t USING btree ((id+1));
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER INDEX。
-- primary-target-begin
ALTER INDEX alterindex_00008_idx ALTER COLUMN 0 SET STATISTICS 1000;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '22023' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS statistics_target_visible FROM pg_catalog.pg_class AS c WHERE c.relname = 'alterindex_00008_idx' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP INDEX IF EXISTS alterindex_00008_idx CASCADE;
DROP TABLE IF EXISTS alterindex_00008_t CASCADE;
