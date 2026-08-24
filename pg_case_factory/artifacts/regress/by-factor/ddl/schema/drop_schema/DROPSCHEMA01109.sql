-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP SCHEMA object_state=exists_with_objects
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPSCHEMA01109
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/drop_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/drop_schema.yaml
-- primary_obligation_id: DROPSCHEMA-EXT|01109|drop_schema|notice_assertion|no_cleanup_needed
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS dropschema_01109_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地 Schema 和因子专用夹具。
CREATE SCHEMA dropschema_01109_sch;
CREATE VIEW dropschema_01109_sch.dropschema_01109_v AS SELECT 1 AS c;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP SCHEMA。
-- primary-target-begin
DROP SCHEMA IF EXISTS dropschema_01109_sch RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS schema_present FROM pg_catalog.pg_namespace WHERE nspname = 'dropschema_01109_sch' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS dropschema_01109_sch CASCADE;
