-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : REINDEX statement_branch=reindex_table
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: REINDEX03265
-- source_md: skills/pg-sql-generation/references/statements/ddl/index/reindex.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/index/reindex.yaml
-- primary_obligation_id: REINDEX-EXT|03265|catalog_validity_check|reindex_concurrently_fix
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS reindex_03265_t, reindex_03265_t_p1 CASCADE;
DROP SCHEMA IF EXISTS reindex_03265_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA reindex_03265_sch;
CREATE TABLE reindex_03265_t (id integer) PARTITION BY RANGE (id);
CREATE TABLE reindex_03265_t_p1 PARTITION OF reindex_03265_t FOR VALUES FROM (0) TO (1000);
-- 3. 执行唯一获得覆盖信用的 REINDEX。
-- primary-target-begin
REINDEX TABLE CONCURRENTLY reindex_03265_sch.reindex_03265_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS table_exists_count FROM pg_catalog.pg_class c WHERE c.relname = 'reindex_03265_t' AND c.relkind = 'r' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS reindex_03265_sch CASCADE;
DROP TABLE IF EXISTS reindex_03265_t, reindex_03265_t_p1 CASCADE;
