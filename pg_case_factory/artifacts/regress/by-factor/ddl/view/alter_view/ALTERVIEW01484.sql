-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER VIEW privilege_level=non_owner_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERVIEW01484
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/alter_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/alter_view.yaml
-- primary_obligation_id: AVIEW-EXT|01484|pg_class_query|revert_alter
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP VIEW IF EXISTS alterview_01484_view;
DROP VIEW IF EXISTS alterview_01484_newschema.alterview_01484_view;
DROP SCHEMA IF EXISTS alterview_01484_newschema CASCADE;
DROP OWNED BY alterview_01484_actor CASCADE;
DROP ROLE IF EXISTS alterview_01484_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterview_01484_actor LOGIN;
CREATE SCHEMA alterview_01484_newschema;
CREATE VIEW alterview_01484_view AS SELECT 1 AS alterview_01484_col, 2 AS alterview_01484_col2;
SET ROLE alterview_01484_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER VIEW。
-- primary-target-begin
ALTER VIEW IF EXISTS alterview_01484_view SET SCHEMA alterview_01484_newschema;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS view_state FROM pg_catalog.pg_class WHERE relname = 'alterview_01484_view' AND relkind = 'v' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP VIEW IF EXISTS alterview_01484_view;
DROP VIEW IF EXISTS alterview_01484_newschema.alterview_01484_view;
DROP SCHEMA IF EXISTS alterview_01484_newschema CASCADE;
DROP OWNED BY alterview_01484_actor CASCADE;
DROP ROLE IF EXISTS alterview_01484_actor;
