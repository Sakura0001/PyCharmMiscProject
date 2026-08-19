-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER INDEX object_state=not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERINDEX00037
-- source_md: skills/pg-sql-generation/references/statements/ddl/index/alter_index.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/index/alter_index.yaml
-- primary_obligation_id: AI-SFV|sfv-4ff9b8ae65c7ef71bb622da2|rename
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterindex_00037_t CASCADE;
DROP INDEX IF EXISTS alterindex_00037_renamed CASCADE;
DROP INDEX IF EXISTS alterindex_00037_idx CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地索引和因子专用夹具。
CREATE TABLE alterindex_00037_t (id integer, tsv tsvector, pt point, rng int4range);
SELECT 1 AS target_index_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER INDEX。
-- primary-target-begin
ALTER INDEX alterindex_00037_idx RENAME TO alterindex_00037_renamed;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P01' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS renamed_index_absent FROM pg_catalog.pg_class AS c JOIN pg_catalog.pg_index AS i ON i.indexrelid = c.oid WHERE c.relname = 'alterindex_00037_renamed' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP INDEX IF EXISTS alterindex_00037_renamed CASCADE;
DROP INDEX IF EXISTS alterindex_00037_idx CASCADE;
DROP TABLE IF EXISTS alterindex_00037_t CASCADE;
