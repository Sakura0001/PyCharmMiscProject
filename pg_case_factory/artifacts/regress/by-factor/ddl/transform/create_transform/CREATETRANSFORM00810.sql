-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TRANSFORM privilege_on_language=no_usage
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETRANSFORM00810
-- source_md: skills/pg-sql-generation/references/statements/ddl/transform/create_transform.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/transform/create_transform.yaml
-- primary_obligation_id: CTR-EXT|00810|catalog_query_pg_transform|drop_transform|all_privilege
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TRANSFORM IF EXISTS FOR createtransform_00810_schema.createtransform_00810_type LANGUAGE plpgsql CASCADE;
DROP FUNCTION IF EXISTS createtransform_00810_schema.createtransform_00810_fromsql(internal) CASCADE;
DROP FUNCTION IF EXISTS createtransform_00810_schema.createtransform_00810_tosql(internal) CASCADE;
DROP TYPE IF EXISTS createtransform_00810_schema.createtransform_00810_type CASCADE;
DROP SCHEMA IF EXISTS createtransform_00810_schema CASCADE;
RESET ROLE;
GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC;
DROP OWNED BY createtransform_00810_actor CASCADE;
DROP ROLE IF EXISTS createtransform_00810_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createtransform_00810_schema;
CREATE TYPE createtransform_00810_schema.createtransform_00810_type AS ENUM ('a');
CREATE FUNCTION createtransform_00810_schema.createtransform_00810_fromsql(internal) RETURNS internal LANGUAGE internal IMMUTABLE STRICT AS 'textlike_support';
CREATE FUNCTION createtransform_00810_schema.createtransform_00810_tosql(internal) RETURNS createtransform_00810_schema.createtransform_00810_type LANGUAGE internal IMMUTABLE STRICT AS 'textlike_support';
CREATE ROLE createtransform_00810_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA createtransform_00810_schema TO createtransform_00810_actor;
GRANT USAGE ON TYPE createtransform_00810_schema.createtransform_00810_type TO createtransform_00810_actor;
REVOKE USAGE ON LANGUAGE plpgsql FROM PUBLIC;
GRANT EXECUTE ON FUNCTION createtransform_00810_schema.createtransform_00810_fromsql(internal) TO createtransform_00810_actor;
GRANT EXECUTE ON FUNCTION createtransform_00810_schema.createtransform_00810_tosql(internal) TO createtransform_00810_actor;
SET ROLE createtransform_00810_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TRANSFORM。
-- primary-target-begin
CREATE TRANSFORM FOR createtransform_00810_schema.createtransform_00810_type LANGUAGE plpgsql (FROM SQL WITH FUNCTION createtransform_00810_schema.createtransform_00810_fromsql(internal), TO SQL WITH FUNCTION createtransform_00810_schema.createtransform_00810_tosql(internal));
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS transform_state FROM pg_catalog.pg_transform WHERE trftype = 'createtransform_00810_type'::regtype AND trflang = (SELECT oid FROM pg_catalog.pg_language WHERE lanname = 'plpgsql') ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC;
DROP TRANSFORM IF EXISTS FOR createtransform_00810_schema.createtransform_00810_type LANGUAGE plpgsql CASCADE;
DROP FUNCTION IF EXISTS createtransform_00810_schema.createtransform_00810_fromsql(internal) CASCADE;
DROP FUNCTION IF EXISTS createtransform_00810_schema.createtransform_00810_tosql(internal) CASCADE;
DROP TYPE IF EXISTS createtransform_00810_schema.createtransform_00810_type CASCADE;
DROP SCHEMA IF EXISTS createtransform_00810_schema CASCADE;
DROP OWNED BY createtransform_00810_actor CASCADE;
DROP ROLE IF EXISTS createtransform_00810_actor;
