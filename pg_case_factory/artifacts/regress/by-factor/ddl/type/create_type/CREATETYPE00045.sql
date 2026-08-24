-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TYPE insufficient_privilege=non_superuser_base_type
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETYPE00045
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/create_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/create_type.yaml
-- primary_obligation_id: CT-SFV|sfv-e2f617f9c9941ac4b0dc6090|define_base_failure
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TYPE IF EXISTS createtype_00045_schema.createtype_00045_type CASCADE;
DROP TYPE IF EXISTS createtype_00045_schema._createtype_00045_type CASCADE;
DROP VIEW IF EXISTS createtype_00045_schema.createtype_00045_type CASCADE;
DROP FUNCTION IF EXISTS createtype_00045_schema.createtype_00045_input(text) CASCADE;
DROP FUNCTION IF EXISTS createtype_00045_schema.createtype_00045_output(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_00045_schema.createtype_00045_receive(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_00045_schema.createtype_00045_send(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_00045_schema.createtype_00045_canon CASCADE;
DROP FUNCTION IF EXISTS createtype_00045_schema.createtype_00045_diff CASCADE;
DROP SCHEMA IF EXISTS createtype_00045_schema CASCADE;
DROP SCHEMA IF EXISTS createtype_00045_noschema CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createtype_00045_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createtype_00045_schema;
CREATE ROLE createtype_00045_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA createtype_00045_schema TO createtype_00045_actor;
SET ROLE createtype_00045_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TYPE。
-- primary-target-begin
CREATE TYPE createtype_00045_schema.createtype_00045_type (INPUT = createtype_00045_schema.createtype_00045_input, OUTPUT = createtype_00045_schema.createtype_00045_output);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS type_state FROM pg_catalog.pg_type WHERE typname = 'createtype_00045_type' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TYPE IF EXISTS createtype_00045_schema.createtype_00045_type;
DROP SCHEMA IF EXISTS createtype_00045_schema CASCADE;
DROP OWNED BY createtype_00045_actor CASCADE;
DROP ROLE IF EXISTS createtype_00045_actor;
