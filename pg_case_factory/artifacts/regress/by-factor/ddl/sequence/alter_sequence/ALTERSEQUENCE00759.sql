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
-- case_id: ALTERSEQUENCE00759
-- source_md: skills/pg-sql-generation/references/statements/ddl/sequence/alter_sequence.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/sequence/alter_sequence.yaml
-- primary_obligation_id: ALTSEQ-EXT|00759|alter_parameters|nextval_call|DROP_SEQUENCE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SEQUENCE IF EXISTS "altersequence_00759_Mixed Seq" CASCADE;
DROP ROLE IF EXISTS altersequence_00759_owner;
DROP ROLE IF EXISTS altersequence_00759_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地序列和因子专用夹具。
CREATE ROLE altersequence_00759_owner LOGIN;
CREATE ROLE altersequence_00759_actor LOGIN;
GRANT USAGE ON SCHEMA public TO altersequence_00759_owner;
GRANT USAGE ON SCHEMA public TO altersequence_00759_actor;
CREATE SEQUENCE "altersequence_00759_Mixed Seq" AS bigint START WITH 1 INCREMENT BY 1;
SET ROLE altersequence_00759_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SEQUENCE。
-- primary-target-begin
ALTER SEQUENCE IF EXISTS "altersequence_00759_Mixed Seq" CACHE 5;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT nextval('altersequence_00759_Mixed Seq') AS nextval_verified;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SEQUENCE IF EXISTS "altersequence_00759_Mixed Seq" CASCADE;
DROP OWNED BY altersequence_00759_owner;
DROP ROLE IF EXISTS altersequence_00759_owner;
DROP OWNED BY altersequence_00759_actor;
DROP ROLE IF EXISTS altersequence_00759_actor;
