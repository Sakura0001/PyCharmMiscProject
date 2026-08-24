-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER INDEX extension=AI-EXT|00210|attach_partition|meta_command|detach_partition
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERINDEX00210
-- source_md: skills/pg-sql-generation/references/statements/ddl/index/alter_index.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/index/alter_index.yaml
-- primary_obligation_id: AI-EXT|00210|attach_partition|meta_command|detach_partition
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterindex_00210_parent, alterindex_00210_part CASCADE;
DROP INDEX IF EXISTS alterindex_00210_parent_idx CASCADE;
DROP INDEX IF EXISTS alterindex_00210_idx CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地索引和因子专用夹具。
CREATE TABLE alterindex_00210_parent (id integer) PARTITION BY RANGE (id);
CREATE TABLE alterindex_00210_part PARTITION OF alterindex_00210_parent FOR VALUES FROM (0) TO (1000);
CREATE INDEX alterindex_00210_parent_idx ON ONLY alterindex_00210_parent (id);
CREATE INDEX alterindex_00210_idx ON alterindex_00210_part (id);
-- 3. 执行唯一获得覆盖信用的 ALTER INDEX。
-- primary-target-begin
ALTER INDEX alterindex_00210_parent_idx ATTACH PARTITION alterindex_00210_idx;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS target_index_visible FROM pg_catalog.pg_class AS c WHERE c.relname = 'alterindex_00210_idx' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP INDEX IF EXISTS alterindex_00210_parent_idx CASCADE;
DROP INDEX IF EXISTS alterindex_00210_idx CASCADE;
DROP TABLE IF EXISTS alterindex_00210_part, alterindex_00210_parent CASCADE;
