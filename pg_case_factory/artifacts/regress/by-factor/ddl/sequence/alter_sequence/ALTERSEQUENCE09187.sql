-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SEQUENCE new_schema_name=non_existing_schema
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSEQUENCE09187
-- source_md: skills/pg-sql-generation/references/statements/ddl/sequence/alter_sequence.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/sequence/alter_sequence.yaml
-- primary_obligation_id: ALTSEQ-EXT|09187|set_schema|currval_call|DROP_SEQUENCE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 3F000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SEQUENCE IF EXISTS altersequence_09187_sch.altersequence_09187_seq CASCADE;
DROP SCHEMA IF EXISTS altersequence_09187_sch CASCADE;
DROP ROLE IF EXISTS altersequence_09187_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地序列和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altersequence_09187_sch;
CREATE ROLE altersequence_09187_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altersequence_09187_owner;
CREATE SEQUENCE altersequence_09187_sch.altersequence_09187_seq AS bigint START WITH 1;
ALTER SEQUENCE altersequence_09187_sch.altersequence_09187_seq OWNER TO altersequence_09187_owner;
SET ROLE altersequence_09187_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SEQUENCE。
-- primary-target-begin
ALTER SEQUENCE IF EXISTS altersequence_09187_sch.altersequence_09187_seq SET SCHEMA altersequence_09187_no_such_sch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '3F000' AS target_sqlstate_matches_expected;
SELECT nextval('altersequence_09187_sch.altersequence_09187_seq') AS nextval_prerequisite;
SELECT currval('altersequence_09187_sch.altersequence_09187_seq') AS currval_verified;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SEQUENCE IF EXISTS altersequence_09187_sch.altersequence_09187_seq CASCADE;
DROP SCHEMA IF EXISTS altersequence_09187_sch CASCADE;
DROP OWNED BY altersequence_09187_owner;
DROP ROLE IF EXISTS altersequence_09187_owner;
