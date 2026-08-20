-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP TRANSFORM privilege_on_type=not_owns_type
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTRANSFORM00032
-- source_md: skills/pg-sql-generation/references/statements/ddl/transform/drop_transform.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/transform/drop_transform.yaml
-- primary_obligation_id: DROPTRANSFORM-SFV|sfv-7deec026cf25564c302f98a9|drop_transform
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TRANSFORM IF EXISTS FOR droptransform_00032_schema.droptransform_00032_type LANGUAGE plpgsql CASCADE;
DROP FUNCTION IF EXISTS droptransform_00032_schema.droptransform_00032_fromsql(internal) CASCADE;
DROP FUNCTION IF EXISTS droptransform_00032_schema.droptransform_00032_tosql(internal) CASCADE;
DROP TYPE IF EXISTS droptransform_00032_schema.droptransform_00032_type CASCADE;
DROP SCHEMA IF EXISTS droptransform_00032_schema CASCADE;
RESET ROLE;
DROP OWNED BY droptransform_00032_actor CASCADE;
DROP ROLE IF EXISTS droptransform_00032_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA droptransform_00032_schema;
CREATE TYPE droptransform_00032_schema.droptransform_00032_type AS ENUM ('a');
CREATE FUNCTION droptransform_00032_schema.droptransform_00032_fromsql(internal) RETURNS internal LANGUAGE internal IMMUTABLE STRICT AS 'textlike_support';
CREATE FUNCTION droptransform_00032_schema.droptransform_00032_tosql(internal) RETURNS droptransform_00032_schema.droptransform_00032_type LANGUAGE internal IMMUTABLE STRICT AS 'textlike_support';
CREATE TRANSFORM FOR droptransform_00032_schema.droptransform_00032_type LANGUAGE plpgsql (FROM SQL WITH FUNCTION droptransform_00032_schema.droptransform_00032_fromsql(internal), TO SQL WITH FUNCTION droptransform_00032_schema.droptransform_00032_tosql(internal));
CREATE ROLE droptransform_00032_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA droptransform_00032_schema TO droptransform_00032_actor;
GRANT USAGE ON TYPE droptransform_00032_schema.droptransform_00032_type TO droptransform_00032_actor;
SET ROLE droptransform_00032_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 DROP TRANSFORM。
-- primary-target-begin
DROP TRANSFORM IF EXISTS FOR droptransform_00032_schema.droptransform_00032_type LANGUAGE plpgsql;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS transform_present FROM pg_catalog.pg_transform t JOIN pg_catalog.pg_language l ON t.trflang = l.oid WHERE t.trftype = 'droptransform_00032_schema.droptransform_00032_type'::regtype AND l.lanname = 'plpgsql' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TRANSFORM IF EXISTS FOR droptransform_00032_schema.droptransform_00032_type LANGUAGE plpgsql CASCADE;
DROP FUNCTION IF EXISTS droptransform_00032_schema.droptransform_00032_fromsql(internal) CASCADE;
DROP FUNCTION IF EXISTS droptransform_00032_schema.droptransform_00032_tosql(internal) CASCADE;
DROP TYPE IF EXISTS droptransform_00032_schema.droptransform_00032_type CASCADE;
DROP SCHEMA IF EXISTS droptransform_00032_schema CASCADE;
DROP OWNED BY droptransform_00032_actor CASCADE;
DROP ROLE IF EXISTS droptransform_00032_actor;
