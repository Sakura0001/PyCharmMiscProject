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
-- case_id: ALTERSEQUENCE08510
-- source_md: skills/pg-sql-generation/references/statements/ddl/sequence/alter_sequence.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/sequence/alter_sequence.yaml
-- primary_obligation_id: ALTSEQ-EXT|08510|rename|nextval_call|DROP_SEQUENCE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SEQUENCE IF EXISTS altersequence_08510_sch.altersequence_08510_seq CASCADE;
DROP SCHEMA IF EXISTS altersequence_08510_sch CASCADE;
DROP ROLE IF EXISTS altersequence_08510_owner;
DROP ROLE IF EXISTS altersequence_08510_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地序列和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altersequence_08510_sch;
CREATE ROLE altersequence_08510_owner LOGIN;
CREATE ROLE altersequence_08510_actor LOGIN;
GRANT USAGE ON SCHEMA public TO altersequence_08510_owner;
GRANT USAGE ON SCHEMA public TO altersequence_08510_actor;
CREATE SEQUENCE altersequence_08510_sch.altersequence_08510_seq AS bigint START WITH 1;
SET ROLE altersequence_08510_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SEQUENCE。
-- primary-target-begin
ALTER SEQUENCE IF EXISTS altersequence_08510_sch.altersequence_08510_seq RENAME TO altersequence_08510_renamed_seq;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT nextval('altersequence_08510_sch.altersequence_08510_seq') AS nextval_verified;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SEQUENCE IF EXISTS altersequence_08510_sch.altersequence_08510_seq CASCADE;
DROP SCHEMA IF EXISTS altersequence_08510_sch CASCADE;
DROP OWNED BY altersequence_08510_owner;
DROP ROLE IF EXISTS altersequence_08510_owner;
DROP OWNED BY altersequence_08510_actor;
DROP ROLE IF EXISTS altersequence_08510_actor;
