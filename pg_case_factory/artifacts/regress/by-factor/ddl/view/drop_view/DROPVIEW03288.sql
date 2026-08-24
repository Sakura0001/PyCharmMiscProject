-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP VIEW dependency_state=has_dependent_views
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPVIEW03288
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/drop_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/drop_view.yaml
-- primary_obligation_id: DROPVIEW-EXT|03288|drop_view|error_assertion|cascade_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropview_03288_vbt CASCADE;
DROP VIEW IF EXISTS "dropview_03288_select" CASCADE;
DROP VIEW IF EXISTS dropview_03288_depv CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE TABLE dropview_03288_vbt (c integer);
CREATE VIEW "dropview_03288_select" AS SELECT * FROM dropview_03288_vbt;
CREATE VIEW dropview_03288_depv AS SELECT * FROM "dropview_03288_select";
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP VIEW。
-- primary-target-begin
DROP VIEW "dropview_03288_select" RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS view_present FROM pg_catalog.pg_class WHERE relname = 'dropview_03288_select' AND relkind = 'v' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP VIEW IF EXISTS "dropview_03288_select" CASCADE;
DROP VIEW IF EXISTS dropview_03288_depv CASCADE;
DROP TABLE IF EXISTS dropview_03288_vbt CASCADE;
