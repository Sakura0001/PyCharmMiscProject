-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP MATERIALIZED VIEW dependency_state=has_dependents
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPMATERIALIZEDVIEW00807
-- source_md: skills/pg-sql-generation/references/statements/ddl/materialized_view/drop_materialized_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/materialized_view/drop_materialized_view.yaml
-- primary_obligation_id: DROPMATERIALIZEDVIEW-EXT|00807|drop_materialized_view|catalog_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropmaterializedview_00807_t CASCADE;
DROP MATERIALIZED VIEW IF EXISTS dropmaterializedview_00807_mv CASCADE;
DROP TABLE IF EXISTS dropmaterializedview_00807_mv CASCADE;
DROP VIEW IF EXISTS dropmaterializedview_00807_depview CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地物化视图和因子专用夹具。
CREATE TABLE dropmaterializedview_00807_t (c integer);
CREATE MATERIALIZED VIEW dropmaterializedview_00807_mv AS SELECT * FROM dropmaterializedview_00807_t;
CREATE VIEW dropmaterializedview_00807_depview AS SELECT * FROM dropmaterializedview_00807_mv;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP MATERIALIZED VIEW。
-- primary-target-begin
DROP MATERIALIZED VIEW IF EXISTS dropmaterializedview_00807_mv;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS matview_present FROM pg_catalog.pg_class WHERE relname = 'dropmaterializedview_00807_mv' AND relkind = 'm' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP MATERIALIZED VIEW IF EXISTS dropmaterializedview_00807_mv CASCADE;
DROP VIEW IF EXISTS dropmaterializedview_00807_depview CASCADE;
DROP TABLE IF EXISTS dropmaterializedview_00807_mv CASCADE;
DROP TABLE IF EXISTS dropmaterializedview_00807_t CASCADE;
