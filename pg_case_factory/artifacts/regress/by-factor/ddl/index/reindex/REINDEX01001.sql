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
-- case_id: REINDEX01001
-- source_md: skills/pg-sql-generation/references/statements/ddl/index/reindex.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/index/reindex.yaml
-- primary_obligation_id: REINDEX-EXT|01001|invalid_index_detection|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS reindex_01001_t CASCADE;
DROP SCHEMA IF EXISTS reindex_01001_sch CASCADE;
DROP ROLE IF EXISTS reindex_01001_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA reindex_01001_sch;
CREATE ROLE reindex_01001_actor LOGIN NOSUPERUSER;
CREATE TABLE reindex_01001_t (id integer);
CREATE INDEX reindex_01001_i ON reindex_01001_t (id);
SET ROLE reindex_01001_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 REINDEX。
-- primary-target-begin
REINDEX INDEX reindex_01001_sch.reindex_01001_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS invalid_index_count FROM pg_catalog.pg_class c JOIN pg_catalog.pg_index i ON i.indexrelid = c.oid WHERE c.relname LIKE 'reindex_01001_%' AND c.relkind = 'i' AND NOT i.indisvalid ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS reindex_01001_sch CASCADE;
DROP OWNED BY reindex_01001_actor;
DROP ROLE IF EXISTS reindex_01001_actor;
DROP TABLE IF EXISTS reindex_01001_t CASCADE;
