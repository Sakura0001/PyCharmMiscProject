-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CLUSTER transaction_block_restriction=cluster_all_inside_transaction_block
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CLUSTER00044
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/cluster.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/cluster.yaml
-- primary_obligation_id: CLUSTER-SFV|sfv-7c9519468cbce246201c49fe|cluster_all
-- expected_outcome: expected_failure
-- expected_sqlstate: 25001
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS cluster_00044_t CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE cluster_00044_t (id integer);
CREATE INDEX cluster_00044_i ON cluster_00044_t (id);
BEGIN;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CLUSTER。
-- primary-target-begin
CLUSTER cluster_00044_t USING cluster_00044_i;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
ROLLBACK;
SELECT :'target_sqlstate' = '25001' AS target_sqlstate_matches_expected;
SELECT count(*) AS clustered_index_count FROM pg_catalog.pg_index i WHERE i.indisclustered AND i.indrelid = (SELECT c.oid FROM pg_catalog.pg_class c WHERE c.relname = 'cluster_00044_t' ORDER BY c.oid LIMIT 1) ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS cluster_00044_t CASCADE;
