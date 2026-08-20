-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : REINDEX permission=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: REINDEX02740
-- source_md: skills/pg-sql-generation/references/statements/ddl/index/reindex.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/index/reindex.yaml
-- primary_obligation_id: REINDEX-EXT|02740|invalid_index_detection|reindex_concurrently_fix
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS reindex_02740_t CASCADE;
DROP SCHEMA IF EXISTS reindex_02740_sch CASCADE;
DROP ROLE IF EXISTS reindex_02740_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA reindex_02740_sch;
CREATE ROLE reindex_02740_actor LOGIN NOSUPERUSER;
CREATE TABLE reindex_02740_t (id integer);
CREATE INDEX reindex_02740_i ON reindex_02740_t (id);
SET ROLE reindex_02740_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 REINDEX。
-- primary-target-begin
REINDEX INDEX CONCURRENTLY reindex_02740_sch.reindex_02740_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS invalid_index_count FROM pg_catalog.pg_class c JOIN pg_catalog.pg_index i ON i.indexrelid = c.oid WHERE c.relname LIKE 'reindex_02740_%' AND c.relkind = 'i' AND NOT i.indisvalid ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS reindex_02740_sch CASCADE;
DROP OWNED BY reindex_02740_actor;
DROP ROLE IF EXISTS reindex_02740_actor;
DROP TABLE IF EXISTS reindex_02740_t CASCADE;
