-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE SEQUENCE privilege_level=non_creator_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATESEQUENCE03903
-- source_md: skills/pg-sql-generation/references/statements/ddl/sequence/create_sequence.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/sequence/create_sequence.yaml
-- primary_obligation_id: CSQ-EXT|03903|sequence_inspection_query|DROP_SEQUENCE_IF_EXISTS|bound_options
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SEQUENCE IF EXISTS createsequence_03903_seq CASCADE;
DROP SCHEMA IF EXISTS createsequence_03903_schema CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createsequence_03903_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createsequence_03903_schema;
CREATE ROLE createsequence_03903_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA createsequence_03903_schema TO createsequence_03903_actor;
SET ROLE createsequence_03903_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE SEQUENCE。
-- primary-target-begin
CREATE UNLOGGED SEQUENCE createsequence_03903_seq MINVALUE 1 MAXVALUE 1000 START WITH 5 CACHE 10;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS seq_state FROM information_schema.sequences WHERE sequence_name = 'createsequence_03903_seq' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SEQUENCE IF EXISTS createsequence_03903_seq CASCADE;
DROP SCHEMA IF EXISTS createsequence_03903_schema CASCADE;
DROP OWNED BY createsequence_03903_actor CASCADE;
DROP ROLE IF EXISTS createsequence_03903_actor;
