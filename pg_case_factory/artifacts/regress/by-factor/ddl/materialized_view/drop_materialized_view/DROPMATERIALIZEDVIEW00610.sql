-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP MATERIALIZED VIEW privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPMATERIALIZEDVIEW00610
-- source_md: skills/pg-sql-generation/references/statements/ddl/materialized_view/drop_materialized_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/materialized_view/drop_materialized_view.yaml
-- primary_obligation_id: DROPMATERIALIZEDVIEW-EXT|00610|drop_materialized_view|effect_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropmaterializedview_00610_t CASCADE;
DROP MATERIALIZED VIEW IF EXISTS dropmaterializedview_00610_mv CASCADE;
DROP TABLE IF EXISTS dropmaterializedview_00610_mv CASCADE;
DROP VIEW IF EXISTS dropmaterializedview_00610_depview CASCADE;
DROP OWNED BY dropmaterializedview_00610_actor;
DROP ROLE IF EXISTS dropmaterializedview_00610_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地物化视图和因子专用夹具。
CREATE ROLE dropmaterializedview_00610_actor LOGIN NOSUPERUSER;
CREATE TABLE dropmaterializedview_00610_t (c integer);
CREATE MATERIALIZED VIEW dropmaterializedview_00610_mv AS SELECT * FROM dropmaterializedview_00610_t;
SET ROLE dropmaterializedview_00610_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP MATERIALIZED VIEW。
-- primary-target-begin
DROP MATERIALIZED VIEW dropmaterializedview_00610_mv RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS matview_present FROM pg_catalog.pg_class WHERE relname = 'dropmaterializedview_00610_mv' AND relkind = 'm' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP MATERIALIZED VIEW IF EXISTS dropmaterializedview_00610_mv CASCADE;
DROP VIEW IF EXISTS dropmaterializedview_00610_depview CASCADE;
DROP OWNED BY dropmaterializedview_00610_actor;
DROP ROLE IF EXISTS dropmaterializedview_00610_actor;
DROP TABLE IF EXISTS dropmaterializedview_00610_mv CASCADE;
DROP TABLE IF EXISTS dropmaterializedview_00610_t CASCADE;
