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
-- case_id: CLUSTER01960
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/cluster.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/cluster.yaml
-- primary_obligation_id: CLUSTER-EXT|01960|pg_class_relclustered|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS cluster_01960_t, cluster_01960_t_p1 CASCADE;
DROP ROLE IF EXISTS cluster_01960_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE ROLE cluster_01960_actor LOGIN NOSUPERUSER;
CREATE TABLE cluster_01960_t (id integer) PARTITION BY RANGE (id);
CREATE TABLE cluster_01960_t_p1 PARTITION OF cluster_01960_t FOR VALUES FROM (0) TO (1000);
CREATE INDEX cluster_01960_i ON cluster_01960_t (id);
CLUSTER cluster_01960_t USING cluster_01960_i;
SET ROLE cluster_01960_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CLUSTER。
-- primary-target-begin
CLUSTER cluster_01960_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS clustered_index_count FROM pg_catalog.pg_index i WHERE i.indisclustered AND i.indrelid = (SELECT c.oid FROM pg_catalog.pg_class c WHERE c.relname = 'cluster_01960_t' ORDER BY c.oid LIMIT 1) ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY cluster_01960_actor;
DROP ROLE IF EXISTS cluster_01960_actor;
DROP TABLE IF EXISTS cluster_01960_t, cluster_01960_t_p1 CASCADE;
