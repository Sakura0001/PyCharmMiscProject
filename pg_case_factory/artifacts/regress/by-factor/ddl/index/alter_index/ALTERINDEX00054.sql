-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER INDEX statistics_value=out_of_range
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERINDEX00054
-- source_md: skills/pg-sql-generation/references/statements/ddl/index/alter_index.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/index/alter_index.yaml
-- primary_obligation_id: AI-SFV|sfv-cb3924434c0f4d555760afaa|set_statistics
-- expected_outcome: expected_failure
-- expected_sqlstate: 22023
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterindex_00054_t CASCADE;
DROP INDEX IF EXISTS alterindex_00054_idx CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地索引和因子专用夹具。
CREATE TABLE alterindex_00054_t (id integer, tsv tsvector, pt point, rng int4range);
CREATE INDEX alterindex_00054_idx ON alterindex_00054_t USING btree ((id+1));
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER INDEX。
-- primary-target-begin
ALTER INDEX alterindex_00054_idx ALTER COLUMN 1 SET STATISTICS -2;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '22023' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS statistics_target_visible FROM pg_catalog.pg_class AS c WHERE c.relname = 'alterindex_00054_idx' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP INDEX IF EXISTS alterindex_00054_idx CASCADE;
DROP TABLE IF EXISTS alterindex_00054_t CASCADE;
