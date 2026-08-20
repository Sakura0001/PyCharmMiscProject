-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TYPE target_form=base
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETYPE01350
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/create_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/create_type.yaml
-- primary_obligation_id: CT-EXT|01350|pg_type_catalog_query|DROP_TYPE_CASCADE|base_options
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TYPE IF EXISTS createtype_01350_schema.createtype_01350_type CASCADE;
DROP TYPE IF EXISTS createtype_01350_schema._createtype_01350_type CASCADE;
DROP VIEW IF EXISTS createtype_01350_schema.createtype_01350_type CASCADE;
DROP FUNCTION IF EXISTS createtype_01350_schema.createtype_01350_input(text) CASCADE;
DROP FUNCTION IF EXISTS createtype_01350_schema.createtype_01350_output(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_01350_schema.createtype_01350_receive(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_01350_schema.createtype_01350_send(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_01350_schema.createtype_01350_canon CASCADE;
DROP FUNCTION IF EXISTS createtype_01350_schema.createtype_01350_diff CASCADE;
DROP SCHEMA IF EXISTS createtype_01350_schema CASCADE;
DROP SCHEMA IF EXISTS createtype_01350_noschema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createtype_01350_schema;
CREATE FUNCTION createtype_01350_schema.createtype_01350_input(text) RETURNS internal AS 'int4in' LANGUAGE internal STRICT;
CREATE FUNCTION createtype_01350_schema.createtype_01350_output(internal) RETURNS text AS 'int4out' LANGUAGE internal STRICT;
CREATE FUNCTION createtype_01350_schema.createtype_01350_receive(internal) RETURNS internal AS 'int4recv' LANGUAGE internal STRICT;
CREATE FUNCTION createtype_01350_schema.createtype_01350_send(internal) RETURNS bytea AS 'int4send' LANGUAGE internal STRICT;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TYPE。
-- primary-target-begin
CREATE TYPE createtype_01350_schema.createtype_01350_type (INPUT = createtype_01350_schema.createtype_01350_input, OUTPUT = createtype_01350_schema.createtype_01350_output, RECEIVE = createtype_01350_schema.createtype_01350_receive, SEND = createtype_01350_schema.createtype_01350_send, INTERNALLENGTH = VARIABLE, ALIGNMENT = int4, STORAGE = extended);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS type_state FROM pg_catalog.pg_type WHERE typname = 'createtype_01350_type' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TYPE IF EXISTS createtype_01350_schema.createtype_01350_type CASCADE;
DROP SCHEMA IF EXISTS createtype_01350_schema CASCADE;
