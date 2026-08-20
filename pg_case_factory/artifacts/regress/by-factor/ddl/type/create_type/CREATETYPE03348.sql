-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TYPE object_state=already_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETYPE03348
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/create_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/create_type.yaml
-- primary_obligation_id: CT-EXT|03348|pg_type_catalog_query|DROP_TYPE_CASCADE|privilege_naming
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TYPE IF EXISTS createtype_03348_schema.createtype_03348_type CASCADE;
DROP TYPE IF EXISTS createtype_03348_schema._createtype_03348_type CASCADE;
DROP VIEW IF EXISTS createtype_03348_schema.createtype_03348_type CASCADE;
DROP FUNCTION IF EXISTS createtype_03348_schema.createtype_03348_input(text) CASCADE;
DROP FUNCTION IF EXISTS createtype_03348_schema.createtype_03348_output(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_03348_schema.createtype_03348_receive(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_03348_schema.createtype_03348_send(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_03348_schema.createtype_03348_canon CASCADE;
DROP FUNCTION IF EXISTS createtype_03348_schema.createtype_03348_diff CASCADE;
DROP SCHEMA IF EXISTS createtype_03348_schema CASCADE;
DROP SCHEMA IF EXISTS createtype_03348_noschema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createtype_03348_schema;
CREATE TYPE createtype_03348_schema."select" AS ENUM ('seed_label');
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TYPE。
-- primary-target-begin
CREATE TYPE createtype_03348_schema."select" AS (col1 integer);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS type_state FROM pg_catalog.pg_type WHERE typname = 'select' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TYPE IF EXISTS createtype_03348_schema."select" CASCADE;
DROP SCHEMA IF EXISTS createtype_03348_schema CASCADE;
