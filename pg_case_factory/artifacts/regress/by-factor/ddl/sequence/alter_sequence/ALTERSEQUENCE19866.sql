-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SEQUENCE owned_by_table_dependency=different_schema
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSEQUENCE19866
-- source_md: skills/pg-sql-generation/references/statements/ddl/sequence/alter_sequence.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/sequence/alter_sequence.yaml
-- primary_obligation_id: ALTSEQ-EXT|19866|alter_parameters|currval_call|DROP_SEQUENCE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altersequence_19866_diff_sch.altersequence_19866_owned_tbl CASCADE;
DROP SEQUENCE IF EXISTS "altersequence_19866_Mixed Seq" CASCADE;
DROP SCHEMA IF EXISTS altersequence_19866_diff_sch CASCADE;
DROP ROLE IF EXISTS altersequence_19866_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地序列和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altersequence_19866_diff_sch;
CREATE ROLE altersequence_19866_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altersequence_19866_owner;
CREATE SEQUENCE "altersequence_19866_Mixed Seq" AS bigint START WITH 1;
CREATE TABLE altersequence_19866_diff_sch.altersequence_19866_owned_tbl (col integer);
ALTER SEQUENCE "altersequence_19866_Mixed Seq" OWNER TO altersequence_19866_owner;
ALTER TABLE altersequence_19866_diff_sch.altersequence_19866_owned_tbl OWNER TO altersequence_19866_owner;
SET ROLE altersequence_19866_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SEQUENCE。
-- primary-target-begin
ALTER SEQUENCE IF EXISTS "altersequence_19866_Mixed Seq" OWNED BY altersequence_19866_diff_sch.altersequence_19866_owned_tbl.col;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT nextval('altersequence_19866_Mixed Seq') AS nextval_prerequisite;
SELECT currval('altersequence_19866_Mixed Seq') AS currval_verified;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SEQUENCE IF EXISTS "altersequence_19866_Mixed Seq" CASCADE;
DROP SCHEMA IF EXISTS altersequence_19866_diff_sch CASCADE;
DROP OWNED BY altersequence_19866_owner;
DROP ROLE IF EXISTS altersequence_19866_owner;
DROP TABLE IF EXISTS altersequence_19866_diff_sch.altersequence_19866_owned_tbl CASCADE;
