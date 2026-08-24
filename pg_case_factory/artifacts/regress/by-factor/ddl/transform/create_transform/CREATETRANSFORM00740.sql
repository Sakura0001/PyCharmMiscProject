-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TRANSFORM target_form=define_transform
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETRANSFORM00740
-- source_md: skills/pg-sql-generation/references/statements/ddl/transform/create_transform.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/transform/create_transform.yaml
-- primary_obligation_id: CTR-EXT|00740|catalog_query_pg_transform|drop_function|direction_function_existence
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TRANSFORM IF EXISTS FOR createtransform_00740_schema.createtransform_00740_type LANGUAGE plpgsql CASCADE;
DROP FUNCTION IF EXISTS createtransform_00740_schema.createtransform_00740_tosql(internal) CASCADE;
DROP TYPE IF EXISTS createtransform_00740_schema.createtransform_00740_type CASCADE;
DROP SCHEMA IF EXISTS createtransform_00740_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createtransform_00740_schema;
CREATE TYPE createtransform_00740_schema.createtransform_00740_type AS ENUM ('a');
CREATE FUNCTION createtransform_00740_schema.createtransform_00740_tosql(internal) RETURNS createtransform_00740_schema.createtransform_00740_type LANGUAGE internal IMMUTABLE STRICT AS 'textlike_support';
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TRANSFORM。
-- primary-target-begin
CREATE OR REPLACE TRANSFORM FOR createtransform_00740_schema.createtransform_00740_type LANGUAGE plpgsql (TO SQL WITH FUNCTION createtransform_00740_schema.createtransform_00740_tosql(internal));
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS transform_state FROM pg_catalog.pg_transform WHERE trftype = 'createtransform_00740_type'::regtype AND trflang = (SELECT oid FROM pg_catalog.pg_language WHERE lanname = 'plpgsql') ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TRANSFORM IF EXISTS FOR createtransform_00740_schema.createtransform_00740_type LANGUAGE plpgsql CASCADE;
DROP FUNCTION IF EXISTS createtransform_00740_schema.createtransform_00740_tosql(internal) CASCADE;
DROP TYPE IF EXISTS createtransform_00740_schema.createtransform_00740_type CASCADE;
DROP SCHEMA IF EXISTS createtransform_00740_schema CASCADE;
