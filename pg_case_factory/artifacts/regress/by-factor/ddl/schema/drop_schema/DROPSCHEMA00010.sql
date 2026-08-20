-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP SCHEMA contained_objects_state=has_multiple_object_types
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPSCHEMA00010
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/drop_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/drop_schema.yaml
-- primary_obligation_id: DROPSCHEMA-SFV|sfv-30ef3200861689ddf3cfc342|drop_schema
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropschema_00010_sch.dropschema_00010_t CASCADE;
DROP SCHEMA IF EXISTS dropschema_00010_sch CASCADE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地 Schema 和因子专用夹具。
CREATE SCHEMA dropschema_00010_sch;
CREATE TABLE dropschema_00010_sch.dropschema_00010_t (c integer);
CREATE VIEW dropschema_00010_sch.dropschema_00010_v AS SELECT 1 AS c;
CREATE FUNCTION dropschema_00010_sch.dropschema_00010_f() RETURNS void AS $$ BEGIN END; $$ LANGUAGE plpgsql;
-- 3. 执行唯一获得覆盖信用的 DROP SCHEMA。
-- primary-target-begin
DROP SCHEMA dropschema_00010_sch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS schema_absent FROM pg_catalog.pg_namespace WHERE nspname = 'dropschema_00010_sch' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS dropschema_00010_sch CASCADE;
DROP TABLE IF EXISTS dropschema_00010_sch.dropschema_00010_t CASCADE;
