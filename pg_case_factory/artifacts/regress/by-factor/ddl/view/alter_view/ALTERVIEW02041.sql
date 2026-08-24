-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER VIEW new_schema_shape=pg_catalog_reserved
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERVIEW02041
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/alter_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/alter_view.yaml
-- primary_obligation_id: AVIEW-EXT|02041|pg_views_query|drop_view_cascade
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP VIEW IF EXISTS alterview_02041_view CASCADE;
DROP OWNED BY alterview_02041_actor CASCADE;
DROP ROLE IF EXISTS alterview_02041_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterview_02041_actor LOGIN;
SET ROLE alterview_02041_actor;
CREATE VIEW alterview_02041_view AS SELECT 1 AS alterview_02041_col, 2 AS alterview_02041_col2;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER VIEW。
-- primary-target-begin
ALTER VIEW alterview_02041_view SET SCHEMA pg_catalog;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS view_state FROM pg_catalog.pg_views WHERE viewname = 'alterview_02041_view' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP VIEW IF EXISTS alterview_02041_view CASCADE;
DROP OWNED BY alterview_02041_actor CASCADE;
DROP ROLE IF EXISTS alterview_02041_actor;
