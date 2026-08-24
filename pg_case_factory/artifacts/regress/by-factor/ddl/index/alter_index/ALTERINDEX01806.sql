-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER INDEX extension=AI-EXT|01806|reset_storage|parameter_check|detach_partition
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERINDEX01806
-- source_md: skills/pg-sql-generation/references/statements/ddl/index/alter_index.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/index/alter_index.yaml
-- primary_obligation_id: AI-EXT|01806|reset_storage|parameter_check|detach_partition
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterindex_01806_src_schema.alterindex_01806_t CASCADE;
DROP INDEX IF EXISTS alterindex_01806_src_schema.alterindex_01806_idx CASCADE;
DROP SCHEMA IF EXISTS alterindex_01806_src_schema CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地索引和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS alterindex_01806_src_schema;
CREATE TABLE alterindex_01806_src_schema.alterindex_01806_t (id integer, tsv tsvector, pt point, rng int4range);
CREATE INDEX alterindex_01806_idx ON alterindex_01806_src_schema.alterindex_01806_t USING brin (id);
-- 3. 执行唯一获得覆盖信用的 ALTER INDEX。
-- primary-target-begin
ALTER INDEX alterindex_01806_src_schema.alterindex_01806_idx RESET (pages_per_range);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS storage_parameter_visible FROM pg_catalog.pg_class AS c JOIN pg_catalog.pg_index AS i ON i.indexrelid = c.oid WHERE c.relname = 'alterindex_01806_idx' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP INDEX IF EXISTS alterindex_01806_src_schema.alterindex_01806_idx CASCADE;
DROP SCHEMA IF EXISTS alterindex_01806_src_schema CASCADE;
DROP TABLE IF EXISTS alterindex_01806_src_schema.alterindex_01806_t CASCADE;
