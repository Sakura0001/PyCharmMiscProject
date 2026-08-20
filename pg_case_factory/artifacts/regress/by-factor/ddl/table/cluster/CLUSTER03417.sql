-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CLUSTER index_dependency=index_not_on_table
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CLUSTER03417
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/cluster.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/cluster.yaml
-- primary_obligation_id: CLUSTER-EXT|03417|pg_class_relclustered|none
-- expected_outcome: expected_failure
-- expected_sqlstate: 42809
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS cluster_03417_sch.cluster_03417_t, cluster_03417_t2 CASCADE;
DROP SCHEMA IF EXISTS cluster_03417_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA cluster_03417_sch;
CREATE TABLE cluster_03417_sch.cluster_03417_t (id integer);
CREATE TABLE cluster_03417_t2 (id integer);
CREATE INDEX cluster_03417_i ON cluster_03417_t2 (id);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CLUSTER。
-- primary-target-begin
CLUSTER VERBOSE cluster_03417_sch.cluster_03417_t USING cluster_03417_i;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42809' AS target_sqlstate_matches_expected;
SELECT count(*) AS clustered_index_count FROM pg_catalog.pg_index i WHERE i.indisclustered AND i.indrelid = (SELECT c.oid FROM pg_catalog.pg_class c WHERE c.relname = 'cluster_03417_t' ORDER BY c.oid LIMIT 1) ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS cluster_03417_sch CASCADE;
DROP TABLE IF EXISTS cluster_03417_sch.cluster_03417_t, cluster_03417_t2 CASCADE;
