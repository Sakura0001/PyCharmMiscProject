-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CLUSTER statement_branch=cluster_all
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CLUSTER00172
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/cluster.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/cluster.yaml
-- primary_obligation_id: CLUSTER-EXT|00172|pg_stat_progress_cluster|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS cluster_00172_t CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE cluster_00172_t (id integer);
CREATE INDEX cluster_00172_i ON cluster_00172_t (id);
CLUSTER cluster_00172_t USING cluster_00172_i;
-- 3. 执行唯一获得覆盖信用的 CLUSTER。
-- primary-target-begin
CLUSTER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS progress_rows FROM pg_catalog.pg_stat_progress_cluster ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS cluster_00172_t CASCADE;
