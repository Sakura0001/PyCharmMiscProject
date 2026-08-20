-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE VIEW target_form=define_view
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEVIEW04951
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/create_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/create_view.yaml
-- primary_obligation_id: CV-EXT|04951|select_from_view|drop_view_cascade|type_colname
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createview_04951_schema.createview_04951_base, createview_04951_schema.createview_04951_join, createview_04951_schema.createview_04951_src CASCADE;
DROP VIEW IF EXISTS createview_04951_schema.createview_04951_view CASCADE;
DROP VIEW IF EXISTS createview_04951_schema.createview_04951_refview CASCADE;
DROP SCHEMA IF EXISTS createview_04951_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createview_04951_schema;
CREATE TABLE createview_04951_schema.createview_04951_base (c1 boolean, c2 boolean, c3 integer);
INSERT INTO createview_04951_schema.createview_04951_base VALUES (true, false, 1);
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE VIEW。
-- primary-target-begin
CREATE VIEW createview_04951_schema.createview_04951_view AS SELECT c1, c2, c3 FROM createview_04951_schema.createview_04951_base;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS view_readable FROM createview_04951_schema.createview_04951_view ORDER BY 1;
-- 5. 清理全部本编号对象。
DROP VIEW createview_04951_schema.createview_04951_view CASCADE;
DROP VIEW IF EXISTS createview_04951_schema.createview_04951_refview CASCADE;
DROP SCHEMA IF EXISTS createview_04951_schema CASCADE;
DROP TABLE IF EXISTS createview_04951_schema.createview_04951_base, createview_04951_schema.createview_04951_join, createview_04951_schema.createview_04951_src CASCADE;
