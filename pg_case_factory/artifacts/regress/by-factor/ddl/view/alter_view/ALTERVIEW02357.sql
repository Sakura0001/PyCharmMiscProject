-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER VIEW new_name_shape=same_as_existing
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERVIEW02357
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/alter_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/alter_view.yaml
-- primary_obligation_id: AVIEW-EXT|02357|pg_views_query|revert_alter
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP VIEW IF EXISTS alterview_02357_view;
DROP VIEW IF EXISTS alterview_02357_conflictview;
DROP VIEW IF EXISTS alterview_02357_conflictview;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE VIEW alterview_02357_view AS SELECT 1 AS alterview_02357_col, 2 AS alterview_02357_col2;
CREATE VIEW alterview_02357_conflictview AS SELECT 1 AS alterview_02357_col;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER VIEW。
-- primary-target-begin
ALTER VIEW alterview_02357_view RENAME TO alterview_02357_conflictview;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS view_state FROM pg_catalog.pg_views WHERE viewname = 'alterview_02357_view' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP VIEW IF EXISTS alterview_02357_view;
DROP VIEW IF EXISTS alterview_02357_conflictview;
DROP VIEW IF EXISTS alterview_02357_conflictview;
