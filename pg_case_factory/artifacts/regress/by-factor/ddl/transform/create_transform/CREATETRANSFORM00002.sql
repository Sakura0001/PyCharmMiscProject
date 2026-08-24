-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TRANSFORM cleanup_mode=drop_function
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETRANSFORM00002
-- source_md: skills/pg-sql-generation/references/statements/ddl/transform/create_transform.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/transform/create_transform.yaml
-- primary_obligation_id: CTR-SFV|sfv-5dcfcdd7e8c7af1154bcdcbc|define_drop_function_cleanup
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TRANSFORM IF EXISTS FOR createtransform_00002_schema.createtransform_00002_type LANGUAGE plpgsql CASCADE;
DROP FUNCTION IF EXISTS createtransform_00002_schema.createtransform_00002_fromsql(internal) CASCADE;
DROP FUNCTION IF EXISTS createtransform_00002_schema.createtransform_00002_tosql(internal) CASCADE;
DROP TYPE IF EXISTS createtransform_00002_schema.createtransform_00002_type CASCADE;
DROP SCHEMA IF EXISTS createtransform_00002_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createtransform_00002_schema;
CREATE TYPE createtransform_00002_schema.createtransform_00002_type AS ENUM ('a');
CREATE FUNCTION createtransform_00002_schema.createtransform_00002_fromsql(internal) RETURNS internal LANGUAGE internal IMMUTABLE STRICT AS 'textlike_support';
CREATE FUNCTION createtransform_00002_schema.createtransform_00002_tosql(internal) RETURNS createtransform_00002_schema.createtransform_00002_type LANGUAGE internal IMMUTABLE STRICT AS 'textlike_support';
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TRANSFORM。
-- primary-target-begin
CREATE TRANSFORM FOR createtransform_00002_schema.createtransform_00002_type LANGUAGE plpgsql (FROM SQL WITH FUNCTION createtransform_00002_schema.createtransform_00002_fromsql(internal), TO SQL WITH FUNCTION createtransform_00002_schema.createtransform_00002_tosql(internal));
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS transform_state FROM pg_catalog.pg_transform WHERE trftype = 'createtransform_00002_type'::regtype AND trflang = (SELECT oid FROM pg_catalog.pg_language WHERE lanname = 'plpgsql') ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TRANSFORM IF EXISTS FOR createtransform_00002_schema.createtransform_00002_type LANGUAGE plpgsql CASCADE;
DROP FUNCTION IF EXISTS createtransform_00002_schema.createtransform_00002_fromsql(internal) CASCADE;
DROP FUNCTION IF EXISTS createtransform_00002_schema.createtransform_00002_tosql(internal) CASCADE;
DROP TYPE IF EXISTS createtransform_00002_schema.createtransform_00002_type CASCADE;
DROP SCHEMA IF EXISTS createtransform_00002_schema CASCADE;
