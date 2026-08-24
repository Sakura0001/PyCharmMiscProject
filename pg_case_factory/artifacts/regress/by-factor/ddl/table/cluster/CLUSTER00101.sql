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
-- case_id: CLUSTER00101
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/cluster.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/cluster.yaml
-- primary_obligation_id: CLUSTER-EXT|00101|pg_stat_progress_cluster|none
-- expected_outcome: expected_failure
-- expected_sqlstate: 25001
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS cluster_00101_t CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE cluster_00101_t (id integer);
CREATE INDEX cluster_00101_i ON cluster_00101_t (id);
CLUSTER cluster_00101_t USING cluster_00101_i;
BEGIN;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CLUSTER。
-- primary-target-begin
CLUSTER VERBOSE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
ROLLBACK;
SELECT :'target_sqlstate' = '25001' AS target_sqlstate_matches_expected;
SELECT count(*) AS progress_rows FROM pg_catalog.pg_stat_progress_cluster ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS cluster_00101_t CASCADE;
