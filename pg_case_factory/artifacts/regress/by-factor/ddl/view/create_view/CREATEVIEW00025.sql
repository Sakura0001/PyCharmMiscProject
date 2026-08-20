-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE VIEW error_boundary=check_option_on_recursive
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEVIEW00025
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/create_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/create_view.yaml
-- primary_obligation_id: CV-SFV|sfv-12972a147ca35bbfc387e68a|define_check_option_on_recursive
-- expected_outcome: expected_failure
-- expected_sqlstate: 42601
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createview_00025_schema.createview_00025_base, createview_00025_schema.createview_00025_join, createview_00025_schema.createview_00025_src CASCADE;
DROP VIEW IF EXISTS createview_00025_schema.createview_00025_view CASCADE;
DROP VIEW IF EXISTS createview_00025_schema.createview_00025_refview CASCADE;
DROP SCHEMA IF EXISTS createview_00025_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createview_00025_schema;
CREATE TABLE createview_00025_schema.createview_00025_base (c1 smallint, c2 integer, c3 bigint);
INSERT INTO createview_00025_schema.createview_00025_base VALUES (1, 100, 2000000);
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE VIEW。
-- primary-target-begin
CREATE RECURSIVE VIEW createview_00025_schema.createview_00025_view (c1, c2, c3) AS SELECT c1, c2, c3 FROM createview_00025_schema.createview_00025_base WITH CASCADED CHECK OPTION;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42601' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS view_state FROM pg_catalog.pg_class WHERE relname = 'createview_00025_view' AND relkind = 'v' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP VIEW IF EXISTS createview_00025_schema.createview_00025_view CASCADE;
DROP VIEW IF EXISTS createview_00025_schema.createview_00025_refview CASCADE;
DROP SCHEMA IF EXISTS createview_00025_schema CASCADE;
DROP TABLE IF EXISTS createview_00025_schema.createview_00025_base, createview_00025_schema.createview_00025_join, createview_00025_schema.createview_00025_src CASCADE;
