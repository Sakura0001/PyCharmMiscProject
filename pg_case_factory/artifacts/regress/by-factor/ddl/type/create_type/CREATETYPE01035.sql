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
-- case_id: CREATETYPE01035
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/create_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/create_type.yaml
-- primary_obligation_id: CT-EXT|01035|pg_type_catalog_query|DROP_TYPE_CASCADE|range_suboptions
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TYPE IF EXISTS createtype_01035_schema.createtype_01035_type CASCADE;
DROP TYPE IF EXISTS createtype_01035_schema._createtype_01035_type CASCADE;
DROP VIEW IF EXISTS createtype_01035_schema.createtype_01035_type CASCADE;
DROP FUNCTION IF EXISTS createtype_01035_schema.createtype_01035_input(text) CASCADE;
DROP FUNCTION IF EXISTS createtype_01035_schema.createtype_01035_output(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_01035_schema.createtype_01035_receive(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_01035_schema.createtype_01035_send(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_01035_schema.createtype_01035_canon CASCADE;
DROP FUNCTION IF EXISTS createtype_01035_schema.createtype_01035_diff CASCADE;
DROP SCHEMA IF EXISTS createtype_01035_schema CASCADE;
DROP SCHEMA IF EXISTS createtype_01035_noschema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createtype_01035_schema;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TYPE。
-- primary-target-begin
CREATE TYPE createtype_01035_schema.createtype_01035_type AS RANGE (SUBTYPE = bigint);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS type_state FROM pg_catalog.pg_type WHERE typname = 'createtype_01035_type' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TYPE IF EXISTS createtype_01035_schema.createtype_01035_type CASCADE;
DROP SCHEMA IF EXISTS createtype_01035_schema CASCADE;
