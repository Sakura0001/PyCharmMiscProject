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
-- case_id: CLUSTER03132
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/cluster.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/cluster.yaml
-- primary_obligation_id: CLUSTER-EXT|03132|pg_stat_progress_cluster|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42809
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS cluster_03132_sch.cluster_03132_t, cluster_03132_t2 CASCADE;
DROP SCHEMA IF EXISTS cluster_03132_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA cluster_03132_sch;
CREATE TABLE cluster_03132_sch.cluster_03132_t (id integer);
CREATE TABLE cluster_03132_t2 (id integer);
CREATE INDEX cluster_03132_i ON cluster_03132_t2 (id);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CLUSTER。
-- primary-target-begin
CLUSTER VERBOSE cluster_03132_sch.cluster_03132_t USING "cluster_03132_i";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42809' AS target_sqlstate_matches_expected;
SELECT count(*) AS progress_rows FROM pg_catalog.pg_stat_progress_cluster ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS cluster_03132_sch CASCADE;
DROP TABLE IF EXISTS cluster_03132_sch.cluster_03132_t, cluster_03132_t2 CASCADE;
