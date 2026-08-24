-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : REINDEX statement_branch=reindex_index
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: REINDEX03231
-- source_md: skills/pg-sql-generation/references/statements/ddl/index/reindex.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/index/reindex.yaml
-- primary_obligation_id: REINDEX-EXT|03231|invalid_index_detection|drop_invalid_index
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS reindex_03231_t CASCADE;
DROP SCHEMA IF EXISTS reindex_03231_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA reindex_03231_sch;
CREATE TABLE reindex_03231_t (id integer);
CREATE INDEX reindex_03231_i ON reindex_03231_t (id);
-- 3. 执行唯一获得覆盖信用的 REINDEX。
-- primary-target-begin
REINDEX INDEX CONCURRENTLY reindex_03231_sch.reindex_03231_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS invalid_index_count FROM pg_catalog.pg_class c JOIN pg_catalog.pg_index i ON i.indexrelid = c.oid WHERE c.relname LIKE 'reindex_03231_%' AND c.relkind = 'i' AND NOT i.indisvalid ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS reindex_03231_sch CASCADE;
DROP TABLE IF EXISTS reindex_03231_t CASCADE;
