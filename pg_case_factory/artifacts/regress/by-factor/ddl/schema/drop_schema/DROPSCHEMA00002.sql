-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP SCHEMA cascade_restrict=cascade
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPSCHEMA00002
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/drop_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/drop_schema.yaml
-- primary_obligation_id: DROPSCHEMA-SFV|sfv-993ffb7ca5c07c261411c759|drop_schema
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS dropschema_00002_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地 Schema 和因子专用夹具。
CREATE SCHEMA dropschema_00002_sch;
-- 3. 执行唯一获得覆盖信用的 DROP SCHEMA。
-- primary-target-begin
DROP SCHEMA dropschema_00002_sch CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS schema_absent FROM pg_catalog.pg_namespace WHERE nspname = 'dropschema_00002_sch' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS dropschema_00002_sch CASCADE;
