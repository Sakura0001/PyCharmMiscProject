-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TYPE insufficient_privilege=non_owner_create
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETYPE00044
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/create_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/create_type.yaml
-- primary_obligation_id: CT-SFV|sfv-d4f0ead871273d4eb8cb9618|define_insufficient_priv
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TYPE IF EXISTS createtype_00044_schema.createtype_00044_type CASCADE;
DROP TYPE IF EXISTS createtype_00044_schema._createtype_00044_type CASCADE;
DROP VIEW IF EXISTS createtype_00044_schema.createtype_00044_type CASCADE;
DROP FUNCTION IF EXISTS createtype_00044_schema.createtype_00044_input(text) CASCADE;
DROP FUNCTION IF EXISTS createtype_00044_schema.createtype_00044_output(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_00044_schema.createtype_00044_receive(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_00044_schema.createtype_00044_send(internal) CASCADE;
DROP FUNCTION IF EXISTS createtype_00044_schema.createtype_00044_canon CASCADE;
DROP FUNCTION IF EXISTS createtype_00044_schema.createtype_00044_diff CASCADE;
DROP SCHEMA IF EXISTS createtype_00044_schema CASCADE;
DROP SCHEMA IF EXISTS createtype_00044_noschema CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createtype_00044_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createtype_00044_schema;
CREATE ROLE createtype_00044_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA createtype_00044_schema TO createtype_00044_actor;
SET ROLE createtype_00044_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TYPE。
-- primary-target-begin
CREATE TYPE createtype_00044_schema.createtype_00044_type AS (col1 integer);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS type_state FROM pg_catalog.pg_type WHERE typname = 'createtype_00044_type' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TYPE IF EXISTS createtype_00044_schema.createtype_00044_type;
DROP SCHEMA IF EXISTS createtype_00044_schema CASCADE;
DROP OWNED BY createtype_00044_actor CASCADE;
DROP ROLE IF EXISTS createtype_00044_actor;
