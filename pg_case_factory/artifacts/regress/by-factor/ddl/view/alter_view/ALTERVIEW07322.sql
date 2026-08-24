-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER VIEW target_action=rename_column
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERVIEW07322
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/alter_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/alter_view.yaml
-- primary_obligation_id: AVIEW-EXT|07322|pg_views_query|revert_alter
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP VIEW IF EXISTS alterview_07322_view;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE VIEW alterview_07322_view AS SELECT 1 AS alterview_07322_col, 2 AS alterview_07322_col2;
-- 3. 执行唯一获得覆盖信用的 ALTER VIEW。
-- primary-target-begin
ALTER VIEW IF EXISTS alterview_07322_view RENAME COLUMN alterview_07322_col TO alterview_07322_newcol;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS view_state FROM pg_catalog.pg_views WHERE viewname = 'alterview_07322_view' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP VIEW IF EXISTS alterview_07322_view;
