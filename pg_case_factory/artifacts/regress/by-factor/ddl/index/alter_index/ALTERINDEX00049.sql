-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER INDEX statement_branch=reset_storage
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERINDEX00049
-- source_md: skills/pg-sql-generation/references/statements/ddl/index/alter_index.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/index/alter_index.yaml
-- primary_obligation_id: AI-SFV|sfv-0cbc93870a271b35a25264eb|reset_storage
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterindex_00049_t CASCADE;
DROP INDEX IF EXISTS alterindex_00049_idx CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地索引和因子专用夹具。
CREATE TABLE alterindex_00049_t (id integer, tsv tsvector, pt point, rng int4range);
CREATE INDEX alterindex_00049_idx ON alterindex_00049_t USING btree (id);
-- 3. 执行唯一获得覆盖信用的 ALTER INDEX。
-- primary-target-begin
ALTER INDEX alterindex_00049_idx RESET (fillfactor);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS storage_parameter_visible FROM pg_catalog.pg_class AS c JOIN pg_catalog.pg_index AS i ON i.indexrelid = c.oid WHERE c.relname = 'alterindex_00049_idx' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP INDEX IF EXISTS alterindex_00049_idx CASCADE;
DROP TABLE IF EXISTS alterindex_00049_t CASCADE;
