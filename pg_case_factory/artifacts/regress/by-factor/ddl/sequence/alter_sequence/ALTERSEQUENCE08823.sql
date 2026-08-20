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
-- case_id: ALTERSEQUENCE08823
-- source_md: skills/pg-sql-generation/references/statements/ddl/sequence/alter_sequence.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/sequence/alter_sequence.yaml
-- primary_obligation_id: ALTSEQ-EXT|08823|set_schema|nextval_call|DROP_SEQUENCE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 3F000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SEQUENCE IF EXISTS "altersequence_08823_Mixed Seq" CASCADE;
DROP ROLE IF EXISTS altersequence_08823_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地序列和因子专用夹具。
CREATE ROLE altersequence_08823_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altersequence_08823_owner;
CREATE SEQUENCE "altersequence_08823_Mixed Seq" AS bigint START WITH 1;
ALTER SEQUENCE "altersequence_08823_Mixed Seq" OWNER TO altersequence_08823_owner;
SET ROLE altersequence_08823_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SEQUENCE。
-- primary-target-begin
ALTER SEQUENCE "altersequence_08823_Mixed Seq" SET SCHEMA altersequence_08823_no_such_sch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '3F000' AS target_sqlstate_matches_expected;
SELECT nextval('altersequence_08823_Mixed Seq') AS nextval_verified;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SEQUENCE IF EXISTS "altersequence_08823_Mixed Seq" CASCADE;
DROP OWNED BY altersequence_08823_owner;
DROP ROLE IF EXISTS altersequence_08823_owner;
