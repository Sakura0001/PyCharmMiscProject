-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CLUSTER verbose_option=paren_verbose_false
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CLUSTER00049
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/cluster.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/cluster.yaml
-- primary_obligation_id: CLUSTER-SFV|sfv-5d745758102682c09204f81f|cluster_paren_option_table_recluster
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS cluster_00049_t CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE cluster_00049_t (id integer);
CREATE INDEX cluster_00049_i ON cluster_00049_t (id);
CLUSTER cluster_00049_t USING cluster_00049_i;
-- 3. 执行唯一获得覆盖信用的 CLUSTER。
-- primary-target-begin
CLUSTER (VERBOSE FALSE) cluster_00049_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS clustered_index_count FROM pg_catalog.pg_index i WHERE i.indisclustered AND i.indrelid = (SELECT c.oid FROM pg_catalog.pg_class c WHERE c.relname = 'cluster_00049_t' ORDER BY c.oid LIMIT 1) ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS cluster_00049_t CASCADE;
