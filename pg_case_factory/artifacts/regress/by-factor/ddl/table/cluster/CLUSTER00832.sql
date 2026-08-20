-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CLUSTER object_state=table_exists_index_does_not_exist
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CLUSTER00832
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/cluster.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/cluster.yaml
-- primary_obligation_id: CLUSTER-EXT|00832|pg_class_relclustered|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS cluster_00832_sch.cluster_00832_t, cluster_00832_t_p1 CASCADE;
DROP SCHEMA IF EXISTS cluster_00832_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA cluster_00832_sch;
CREATE TABLE cluster_00832_sch.cluster_00832_t (id integer) PARTITION BY RANGE (id);
CREATE TABLE cluster_00832_t_p1 PARTITION OF cluster_00832_sch.cluster_00832_t FOR VALUES FROM (0) TO (1000);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CLUSTER。
-- primary-target-begin
CLUSTER (VERBOSE TRUE) cluster_00832_sch.cluster_00832_t USING cluster_00832_no_such_index;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) AS clustered_index_count FROM pg_catalog.pg_index i WHERE i.indisclustered AND i.indrelid = (SELECT c.oid FROM pg_catalog.pg_class c WHERE c.relname = 'cluster_00832_t' ORDER BY c.oid LIMIT 1) ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS cluster_00832_sch CASCADE;
DROP TABLE IF EXISTS cluster_00832_sch.cluster_00832_t, cluster_00832_t_p1 CASCADE;
