-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SEQUENCE privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSEQUENCE21537
-- source_md: skills/pg-sql-generation/references/statements/ddl/sequence/alter_sequence.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/sequence/alter_sequence.yaml
-- primary_obligation_id: ALTSEQ-EXT|21537|alter_parameters|pg_class_catalog_query|DROP_SEQUENCE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SEQUENCE IF EXISTS "altersequence_21537_Mixed Seq" CASCADE;
DROP ROLE IF EXISTS altersequence_21537_owner;
DROP ROLE IF EXISTS altersequence_21537_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地序列和因子专用夹具。
CREATE ROLE altersequence_21537_owner LOGIN;
CREATE ROLE altersequence_21537_actor LOGIN;
GRANT USAGE ON SCHEMA public TO altersequence_21537_owner;
GRANT USAGE ON SCHEMA public TO altersequence_21537_actor;
CREATE SEQUENCE "altersequence_21537_Mixed Seq" AS bigint START WITH 1 INCREMENT BY 1;
SET ROLE altersequence_21537_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SEQUENCE。
-- primary-target-begin
ALTER SEQUENCE IF EXISTS "altersequence_21537_Mixed Seq" START 1;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS seq_exists FROM pg_catalog.pg_class WHERE relname = 'altersequence_21537_Mixed Seq' AND relkind = 'S' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SEQUENCE IF EXISTS "altersequence_21537_Mixed Seq" CASCADE;
DROP OWNED BY altersequence_21537_owner;
DROP ROLE IF EXISTS altersequence_21537_owner;
DROP OWNED BY altersequence_21537_actor;
DROP ROLE IF EXISTS altersequence_21537_actor;
