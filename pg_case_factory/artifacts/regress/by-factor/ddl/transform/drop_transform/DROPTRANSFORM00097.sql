-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP TRANSFORM object_state=absent
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTRANSFORM00097
-- source_md: skills/pg-sql-generation/references/statements/ddl/transform/drop_transform.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/transform/drop_transform.yaml
-- primary_obligation_id: DROPTRANSFORM-EXT|00097|drop_transform|catalog_query|drop_transform
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TRANSFORM IF EXISTS FOR droptransform_00097_schema.droptransform_00097_type LANGUAGE plpgsql CASCADE;
DROP TYPE IF EXISTS droptransform_00097_schema.droptransform_00097_type CASCADE;
DROP SCHEMA IF EXISTS droptransform_00097_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA droptransform_00097_schema;
CREATE TYPE droptransform_00097_schema.droptransform_00097_type AS ENUM ('a');
SELECT 1 AS target_transform_intentionally_absent;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 DROP TRANSFORM。
-- primary-target-begin
DROP TRANSFORM FOR droptransform_00097_schema.droptransform_00097_type LANGUAGE plpgsql;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS transform_absent FROM pg_catalog.pg_transform t JOIN pg_catalog.pg_language l ON t.trflang = l.oid WHERE t.trftype = 'droptransform_00097_schema.droptransform_00097_type'::regtype AND l.lanname = 'plpgsql' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TRANSFORM IF EXISTS FOR droptransform_00097_schema.droptransform_00097_type LANGUAGE plpgsql CASCADE;
DROP TYPE IF EXISTS droptransform_00097_schema.droptransform_00097_type CASCADE;
DROP SCHEMA IF EXISTS droptransform_00097_schema CASCADE;
