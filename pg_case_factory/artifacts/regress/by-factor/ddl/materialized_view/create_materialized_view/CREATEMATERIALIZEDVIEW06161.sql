-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE MATERIALIZED VIEW target_action=create_matview
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEMATERIALIZEDVIEW06161
-- source_md: skills/pg-sql-generation/references/statements/ddl/materialized_view/create_materialized_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/materialized_view/create_materialized_view.yaml
-- primary_obligation_id: CMATVIEW-EXT|06161|catalog_query|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP MATERIALIZED VIEW IF EXISTS "creatematerializedview_06161_mv";
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
-- 3. 执行唯一获得覆盖信用的 CREATE MATERIALIZED VIEW。
-- primary-target-begin
CREATE MATERIALIZED VIEW IF NOT EXISTS "creatematerializedview_06161_mv" AS WITH creatematerializedview_06161_cte AS (SELECT 1 AS c1, 2 AS c2) SELECT c1, c2 FROM creatematerializedview_06161_cte WITH NO DATA;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS mv_present FROM pg_catalog.pg_matviews WHERE matviewname = 'creatematerializedview_06161_mv' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP MATERIALIZED VIEW IF EXISTS "creatematerializedview_06161_mv";
