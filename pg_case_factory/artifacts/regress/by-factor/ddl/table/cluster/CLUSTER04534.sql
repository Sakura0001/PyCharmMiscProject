-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CLUSTER statement_branch=cluster_verbose_table_recluster
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CLUSTER04534
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/cluster.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/cluster.yaml
-- primary_obligation_id: CLUSTER-EXT|04534|error_assertion|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS cluster_04534_t, cluster_04534_t_p1 CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE cluster_04534_t (id integer) PARTITION BY RANGE (id);
CREATE TABLE cluster_04534_t_p1 PARTITION OF cluster_04534_t FOR VALUES FROM (0) TO (1000);
CREATE INDEX cluster_04534_i ON cluster_04534_t (id);
CLUSTER cluster_04534_t USING cluster_04534_i;
-- 3. 执行唯一获得覆盖信用的 CLUSTER。
-- primary-target-begin
CLUSTER VERBOSE cluster_04534_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS cluster_04534_t, cluster_04534_t_p1 CASCADE;
