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
-- case_id: REINDEX00180
-- source_md: skills/pg-sql-generation/references/statements/ddl/index/reindex.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/index/reindex.yaml
-- primary_obligation_id: REINDEX-EXT|00180|catalog_validity_check|drop_invalid_index
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS reindex_00180_t CASCADE;
DROP ROLE IF EXISTS reindex_00180_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE ROLE reindex_00180_actor LOGIN NOSUPERUSER;
CREATE TABLE reindex_00180_t (id integer);
CREATE INDEX reindex_00180_i ON reindex_00180_t (id);
SET ROLE reindex_00180_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 REINDEX。
-- primary-target-begin
REINDEX INDEX "reindex_00180_t";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS index_validity_count FROM pg_catalog.pg_class c JOIN pg_catalog.pg_index i ON i.indexrelid = c.oid WHERE c.relname = 'reindex_00180_i' AND c.relkind = 'i' AND i.indisvalid ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY reindex_00180_actor;
DROP ROLE IF EXISTS reindex_00180_actor;
DROP TABLE IF EXISTS reindex_00180_t CASCADE;
