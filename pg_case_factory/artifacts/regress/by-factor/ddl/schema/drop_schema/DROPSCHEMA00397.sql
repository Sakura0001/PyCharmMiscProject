-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP SCHEMA privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPSCHEMA00397
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/drop_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/drop_schema.yaml
-- primary_obligation_id: DROPSCHEMA-EXT|00397|drop_schema|information_schema_schemata|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS dropschema_00397_sch CASCADE;
DROP OWNED BY dropschema_00397_actor;
DROP ROLE IF EXISTS dropschema_00397_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地 Schema 和因子专用夹具。
CREATE ROLE dropschema_00397_actor LOGIN NOSUPERUSER;
CREATE SCHEMA dropschema_00397_sch;
CREATE VIEW dropschema_00397_sch.dropschema_00397_v AS SELECT 1 AS c;
SET ROLE dropschema_00397_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP SCHEMA。
-- primary-target-begin
DROP SCHEMA dropschema_00397_sch CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS schema_present FROM pg_catalog.pg_namespace WHERE nspname = 'dropschema_00397_sch' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS dropschema_00397_sch CASCADE;
DROP OWNED BY dropschema_00397_actor;
DROP ROLE IF EXISTS dropschema_00397_actor;
