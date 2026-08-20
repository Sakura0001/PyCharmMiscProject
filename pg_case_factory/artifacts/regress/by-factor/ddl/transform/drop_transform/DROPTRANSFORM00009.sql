-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP TRANSFORM dependent_object_exists=has_dependencies
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTRANSFORM00009
-- source_md: skills/pg-sql-generation/references/statements/ddl/transform/drop_transform.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/transform/drop_transform.yaml
-- primary_obligation_id: DROPTRANSFORM-SFV|sfv-6ef8908006f69e3bd66cce70|drop_transform
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TRANSFORM IF EXISTS FOR droptransform_00009_schema.droptransform_00009_type LANGUAGE plpgsql CASCADE;
DROP FUNCTION IF EXISTS droptransform_00009_schema.droptransform_00009_fromsql(internal) CASCADE;
DROP FUNCTION IF EXISTS droptransform_00009_schema.droptransform_00009_tosql(internal) CASCADE;
DROP TYPE IF EXISTS droptransform_00009_schema.droptransform_00009_type CASCADE;
DROP SCHEMA IF EXISTS droptransform_00009_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA droptransform_00009_schema;
CREATE TYPE droptransform_00009_schema.droptransform_00009_type AS ENUM ('a');
CREATE FUNCTION droptransform_00009_schema.droptransform_00009_fromsql(internal) RETURNS internal LANGUAGE internal IMMUTABLE STRICT AS 'textlike_support';
CREATE FUNCTION droptransform_00009_schema.droptransform_00009_tosql(internal) RETURNS droptransform_00009_schema.droptransform_00009_type LANGUAGE internal IMMUTABLE STRICT AS 'textlike_support';
CREATE TRANSFORM FOR droptransform_00009_schema.droptransform_00009_type LANGUAGE plpgsql (FROM SQL WITH FUNCTION droptransform_00009_schema.droptransform_00009_fromsql(internal), TO SQL WITH FUNCTION droptransform_00009_schema.droptransform_00009_tosql(internal));
SELECT 1 AS dependent_context_armed;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 DROP TRANSFORM。
-- primary-target-begin
DROP TRANSFORM IF EXISTS FOR droptransform_00009_schema.droptransform_00009_type LANGUAGE plpgsql RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS transform_present FROM pg_catalog.pg_transform t JOIN pg_catalog.pg_language l ON t.trflang = l.oid WHERE t.trftype = 'droptransform_00009_schema.droptransform_00009_type'::regtype AND l.lanname = 'plpgsql' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TRANSFORM IF EXISTS FOR droptransform_00009_schema.droptransform_00009_type LANGUAGE plpgsql CASCADE;
DROP FUNCTION IF EXISTS droptransform_00009_schema.droptransform_00009_fromsql(internal) CASCADE;
DROP FUNCTION IF EXISTS droptransform_00009_schema.droptransform_00009_tosql(internal) CASCADE;
DROP TYPE IF EXISTS droptransform_00009_schema.droptransform_00009_type CASCADE;
DROP SCHEMA IF EXISTS droptransform_00009_schema CASCADE;
