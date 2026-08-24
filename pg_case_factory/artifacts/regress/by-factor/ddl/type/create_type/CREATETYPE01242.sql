-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TYPE target_form=range
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETYPE01242
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/create_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/create_type.yaml
-- primary_obligation_id: CT-EXT|01242|pg_type_catalog_query|DROP_TYPE_CASCADE|range_suboptions
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TYPE IF EXISTS createtype_01242_schema.createtype_01242_type CASCADE;
DROP TYPE IF EXISTS createtype_01242_schema._createtype_01242_type CASCADE;
DROP VIEW IF EXISTS createtype_01242_schema.createtype_01242_type CASCADE;
DROP FUNCTION IF EXISTS createtype_01242_schema.createtype_01242_input(text) CASCADE;
DROP FUNCTION IF EXISTS createtype_01242_schema.createtype_01242_output(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_01242_schema.createtype_01242_receive(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_01242_schema.createtype_01242_send(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_01242_schema.createtype_01242_canon CASCADE;
DROP FUNCTION IF EXISTS createtype_01242_schema.createtype_01242_diff CASCADE;
DROP SCHEMA IF EXISTS createtype_01242_schema CASCADE;
DROP SCHEMA IF EXISTS createtype_01242_noschema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createtype_01242_schema;
CREATE TYPE createtype_01242_schema.createtype_01242_type;
CREATE FUNCTION createtype_01242_schema.createtype_01242_canon(createtype_01242_schema.createtype_01242_type) RETURNS createtype_01242_schema.createtype_01242_type LANGUAGE plpgsql AS '$$ BEGIN RETURN $1; END; $$';
CREATE FUNCTION createtype_01242_schema.createtype_01242_diff(createtype_01242_schema.createtype_01242_type, createtype_01242_schema.createtype_01242_type) RETURNS double precision LANGUAGE plpgsql AS '$$ BEGIN RETURN 0.0; END; $$';
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TYPE。
-- primary-target-begin
CREATE TYPE createtype_01242_schema.createtype_01242_type AS RANGE (SUBTYPE = timestamptz, SUBTYPE_DIFF = createtype_01242_schema.createtype_01242_diff);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS type_state FROM pg_catalog.pg_type WHERE typname = 'createtype_01242_type' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TYPE IF EXISTS createtype_01242_schema.createtype_01242_type CASCADE;
DROP SCHEMA IF EXISTS createtype_01242_schema CASCADE;
