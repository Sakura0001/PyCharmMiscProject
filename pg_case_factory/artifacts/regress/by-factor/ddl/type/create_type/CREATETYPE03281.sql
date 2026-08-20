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
-- case_id: CREATETYPE03281
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/create_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/create_type.yaml
-- primary_obligation_id: CT-EXT|03281|SELECT_type_query|DROP_TYPE_IF_EXISTS|privilege_naming
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TYPE IF EXISTS createtype_03281_schema.createtype_03281_type CASCADE;
DROP TYPE IF EXISTS createtype_03281_schema._createtype_03281_type CASCADE;
DROP VIEW IF EXISTS createtype_03281_schema.createtype_03281_type CASCADE;
DROP FUNCTION IF EXISTS createtype_03281_schema.createtype_03281_input(text) CASCADE;
DROP FUNCTION IF EXISTS createtype_03281_schema.createtype_03281_output(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_03281_schema.createtype_03281_receive(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_03281_schema.createtype_03281_send(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_03281_schema.createtype_03281_canon CASCADE;
DROP FUNCTION IF EXISTS createtype_03281_schema.createtype_03281_diff CASCADE;
DROP SCHEMA IF EXISTS createtype_03281_schema CASCADE;
DROP SCHEMA IF EXISTS createtype_03281_noschema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createtype_03281_schema;
CREATE TYPE createtype_03281_schema.createtype_03281_type AS ENUM ('seed_label');
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TYPE。
-- primary-target-begin
CREATE TYPE createtype_03281_schema.createtype_03281_type AS (col1 integer);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS type_state FROM pg_catalog.pg_type WHERE typname = 'createtype_03281_type' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TYPE IF EXISTS createtype_03281_schema.createtype_03281_type;
DROP SCHEMA IF EXISTS createtype_03281_schema CASCADE;
