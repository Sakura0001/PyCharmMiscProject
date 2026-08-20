-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TRANSFORM duplicate_transform=existing_transform_without_or_replace
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETRANSFORM00293
-- source_md: skills/pg-sql-generation/references/statements/ddl/transform/create_transform.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/transform/create_transform.yaml
-- primary_obligation_id: CTR-EXT|00293|error_assertion|drop_function|type_existence
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TRANSFORM IF EXISTS FOR createtransform_00293_schema.createtransform_00293_type LANGUAGE plpgsql CASCADE;
DROP FUNCTION IF EXISTS createtransform_00293_schema.createtransform_00293_fromsql(internal) CASCADE;
DROP FUNCTION IF EXISTS createtransform_00293_schema.createtransform_00293_tosql(internal) CASCADE;
DROP TYPE IF EXISTS createtransform_00293_schema.createtransform_00293_type CASCADE;
DROP SCHEMA IF EXISTS createtransform_00293_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createtransform_00293_schema;
CREATE FUNCTION createtransform_00293_schema.createtransform_00293_fromsql(internal) RETURNS internal LANGUAGE internal IMMUTABLE STRICT AS 'textlike_support';
CREATE FUNCTION createtransform_00293_schema.createtransform_00293_tosql(internal) RETURNS createtransform_00293_schema.createtransform_00293_type LANGUAGE internal IMMUTABLE STRICT AS 'textlike_support';
CREATE TRANSFORM FOR createtransform_00293_schema.createtransform_00293_type LANGUAGE plpgsql (FROM SQL WITH FUNCTION createtransform_00293_schema.createtransform_00293_fromsql(internal), TO SQL WITH FUNCTION createtransform_00293_schema.createtransform_00293_tosql(internal));
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TRANSFORM。
-- primary-target-begin
CREATE TRANSFORM FOR createtransform_00293_schema.createtransform_00293_type LANGUAGE plpgsql (FROM SQL WITH FUNCTION createtransform_00293_schema.createtransform_00293_fromsql(internal), TO SQL WITH FUNCTION createtransform_00293_schema.createtransform_00293_tosql(internal));
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TRANSFORM IF EXISTS FOR createtransform_00293_schema.createtransform_00293_type LANGUAGE plpgsql CASCADE;
DROP FUNCTION IF EXISTS createtransform_00293_schema.createtransform_00293_fromsql(internal) CASCADE;
DROP FUNCTION IF EXISTS createtransform_00293_schema.createtransform_00293_tosql(internal) CASCADE;
DROP TYPE IF EXISTS createtransform_00293_schema.createtransform_00293_type CASCADE;
DROP SCHEMA IF EXISTS createtransform_00293_schema CASCADE;
