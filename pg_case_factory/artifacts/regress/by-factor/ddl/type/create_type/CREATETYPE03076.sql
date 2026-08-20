-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TYPE missing_required_functions=no_input_function
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETYPE03076
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/create_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/create_type.yaml
-- primary_obligation_id: CT-EXT|03076|pg_type_catalog_query|DROP_TYPE|base_boundary
-- expected_outcome: expected_failure
-- expected_sqlstate: 42883
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TYPE IF EXISTS createtype_03076_schema.createtype_03076_type CASCADE;
DROP TYPE IF EXISTS createtype_03076_schema._createtype_03076_type CASCADE;
DROP VIEW IF EXISTS createtype_03076_schema.createtype_03076_type CASCADE;
DROP FUNCTION IF EXISTS createtype_03076_schema.createtype_03076_input(text) CASCADE;
DROP FUNCTION IF EXISTS createtype_03076_schema.createtype_03076_output(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_03076_schema.createtype_03076_receive(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_03076_schema.createtype_03076_send(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_03076_schema.createtype_03076_canon CASCADE;
DROP FUNCTION IF EXISTS createtype_03076_schema.createtype_03076_diff CASCADE;
DROP SCHEMA IF EXISTS createtype_03076_schema CASCADE;
DROP SCHEMA IF EXISTS createtype_03076_noschema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createtype_03076_schema;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TYPE。
-- primary-target-begin
CREATE TYPE createtype_03076_schema.createtype_03076_type (INPUT = createtype_03076_bogus_input, OUTPUT = createtype_03076_bogus_output, RECEIVE = createtype_03076_schema.createtype_03076_receive, SEND = createtype_03076_schema.createtype_03076_send);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42883' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS type_state FROM pg_catalog.pg_type WHERE typname = 'createtype_03076_type' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TYPE createtype_03076_schema.createtype_03076_type;
DROP SCHEMA IF EXISTS createtype_03076_schema CASCADE;
