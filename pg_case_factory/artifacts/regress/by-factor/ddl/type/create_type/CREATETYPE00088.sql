-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TYPE type_name_shape=schema_qualified
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETYPE00088
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/create_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/create_type.yaml
-- primary_obligation_id: CT-SFV|sfv-559159501b5c4cf0a2f1ab5c|define_schema_qualified
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TYPE IF EXISTS createtype_00088_schema.createtype_00088_type CASCADE;
DROP TYPE IF EXISTS createtype_00088_schema._createtype_00088_type CASCADE;
DROP VIEW IF EXISTS createtype_00088_schema.createtype_00088_type CASCADE;
DROP FUNCTION IF EXISTS createtype_00088_schema.createtype_00088_input(text) CASCADE;
DROP FUNCTION IF EXISTS createtype_00088_schema.createtype_00088_output(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_00088_schema.createtype_00088_receive(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_00088_schema.createtype_00088_send(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_00088_schema.createtype_00088_canon CASCADE;
DROP FUNCTION IF EXISTS createtype_00088_schema.createtype_00088_diff CASCADE;
DROP SCHEMA IF EXISTS createtype_00088_schema CASCADE;
DROP SCHEMA IF EXISTS createtype_00088_noschema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createtype_00088_schema;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TYPE。
-- primary-target-begin
CREATE TYPE createtype_00088_schema.createtype_00088_type AS (col1 integer);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS type_state FROM pg_catalog.pg_type WHERE typname = 'createtype_00088_type' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TYPE IF EXISTS createtype_00088_schema.createtype_00088_type;
DROP SCHEMA IF EXISTS createtype_00088_schema CASCADE;
