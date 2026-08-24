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
-- case_id: CREATESEQUENCE05995
-- source_md: skills/pg-sql-generation/references/statements/ddl/sequence/create_sequence.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/sequence/create_sequence.yaml
-- primary_obligation_id: CSQ-EXT|05995|pg_class_catalog_query|DROP_SEQUENCE_CASCADE|naming_options
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SEQUENCE IF EXISTS "select" CASCADE;
DROP SCHEMA IF EXISTS createsequence_05995_schema CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createsequence_05995_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createsequence_05995_schema;
CREATE ROLE createsequence_05995_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA createsequence_05995_schema TO createsequence_05995_actor;
SET ROLE createsequence_05995_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE SEQUENCE。
-- primary-target-begin
CREATE UNLOGGED SEQUENCE "select";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS seq_state FROM pg_catalog.pg_class WHERE relname = 'select' AND relkind = 'S' AND relnamespace = 'createsequence_05995_schema'::regnamespace ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SEQUENCE "select" CASCADE;
DROP SCHEMA IF EXISTS createsequence_05995_schema CASCADE;
DROP OWNED BY createsequence_05995_actor CASCADE;
DROP ROLE IF EXISTS createsequence_05995_actor;
