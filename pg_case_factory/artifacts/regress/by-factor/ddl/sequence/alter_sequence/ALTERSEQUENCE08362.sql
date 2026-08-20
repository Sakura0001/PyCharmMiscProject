-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SEQUENCE new_owner_shape=non_existing_role
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSEQUENCE08362
-- source_md: skills/pg-sql-generation/references/statements/ddl/sequence/alter_sequence.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/sequence/alter_sequence.yaml
-- primary_obligation_id: ALTSEQ-EXT|08362|owner|pg_class_catalog_query|DROP_SEQUENCE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SEQUENCE IF EXISTS altersequence_08362_sch.altersequence_08362_seq CASCADE;
DROP SCHEMA IF EXISTS altersequence_08362_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地序列和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altersequence_08362_sch;
CREATE SEQUENCE altersequence_08362_sch.altersequence_08362_seq AS bigint START WITH 1;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SEQUENCE。
-- primary-target-begin
ALTER SEQUENCE IF EXISTS altersequence_08362_sch.altersequence_08362_seq OWNER TO SESSION_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) AS seq_exists FROM pg_catalog.pg_class WHERE relname = 'altersequence_08362_sch.altersequence_08362_seq' AND relkind = 'S' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP SEQUENCE IF EXISTS altersequence_08362_sch.altersequence_08362_seq CASCADE;
DROP SCHEMA IF EXISTS altersequence_08362_sch CASCADE;
