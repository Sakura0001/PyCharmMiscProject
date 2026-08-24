-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TYPE target_form=enum
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETYPE00939
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/create_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/create_type.yaml
-- primary_obligation_id: CT-EXT|00939|information_schema_user_defined_types|DROP_TYPE_CASCADE|enum_labels
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TYPE IF EXISTS createtype_00939_schema.createtype_00939_type CASCADE;
DROP TYPE IF EXISTS createtype_00939_schema._createtype_00939_type CASCADE;
DROP VIEW IF EXISTS createtype_00939_schema.createtype_00939_type CASCADE;
DROP FUNCTION IF EXISTS createtype_00939_schema.createtype_00939_input(text) CASCADE;
DROP FUNCTION IF EXISTS createtype_00939_schema.createtype_00939_output(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_00939_schema.createtype_00939_receive(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_00939_schema.createtype_00939_send(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_00939_schema.createtype_00939_canon CASCADE;
DROP FUNCTION IF EXISTS createtype_00939_schema.createtype_00939_diff CASCADE;
DROP SCHEMA IF EXISTS createtype_00939_schema CASCADE;
DROP SCHEMA IF EXISTS createtype_00939_noschema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createtype_00939_schema;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TYPE。
-- primary-target-begin
CREATE TYPE createtype_00939_schema.createtype_00939_type AS ENUM ('label1');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS type_state FROM information_schema.user_defined_types WHERE user_defined_type_name = 'createtype_00939_type' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TYPE IF EXISTS createtype_00939_schema.createtype_00939_type CASCADE;
DROP SCHEMA IF EXISTS createtype_00939_schema CASCADE;
