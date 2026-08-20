-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CLUSTER privilege_level=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CLUSTER02122
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/cluster.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/cluster.yaml
-- primary_obligation_id: CLUSTER-EXT|02122|physical_ordering_check|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS cluster_02122_sch.cluster_02122_t, cluster_02122_t_p1 CASCADE;
DROP SCHEMA IF EXISTS cluster_02122_sch CASCADE;
DROP ROLE IF EXISTS cluster_02122_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA cluster_02122_sch;
CREATE ROLE cluster_02122_actor LOGIN NOSUPERUSER;
CREATE TABLE cluster_02122_sch.cluster_02122_t (id integer) PARTITION BY RANGE (id);
CREATE TABLE cluster_02122_t_p1 PARTITION OF cluster_02122_sch.cluster_02122_t FOR VALUES FROM (0) TO (1000);
CREATE INDEX cluster_02122_i ON cluster_02122_sch.cluster_02122_t (id);
SET ROLE cluster_02122_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CLUSTER。
-- primary-target-begin
CLUSTER VERBOSE cluster_02122_sch.cluster_02122_t USING cluster_02122_i;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS physical_order_probe FROM pg_catalog.pg_class c WHERE c.relname = 'cluster_02122_t' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS cluster_02122_sch CASCADE;
DROP OWNED BY cluster_02122_actor;
DROP ROLE IF EXISTS cluster_02122_actor;
DROP TABLE IF EXISTS cluster_02122_sch.cluster_02122_t, cluster_02122_t_p1 CASCADE;
