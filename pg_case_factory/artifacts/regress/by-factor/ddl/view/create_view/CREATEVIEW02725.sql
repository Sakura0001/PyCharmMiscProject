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
-- case_id: CREATEVIEW02725
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/create_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/create_view.yaml
-- primary_obligation_id: CV-EXT|02725|pg_class_query|drop_view_cascade|branch_query
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createview_02725_schema.createview_02725_base, createview_02725_schema.createview_02725_join, createview_02725_schema.createview_02725_src CASCADE;
DROP VIEW IF EXISTS createview_02725_schema.createview_02725_view CASCADE;
DROP VIEW IF EXISTS createview_02725_schema.createview_02725_refview CASCADE;
DROP SCHEMA IF EXISTS createview_02725_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createview_02725_schema;
CREATE TABLE createview_02725_schema.createview_02725_base (c1 smallint, c2 integer, c3 bigint);
INSERT INTO createview_02725_schema.createview_02725_base VALUES (1, 100, 2000000);
CREATE TABLE createview_02725_schema.createview_02725_src (c1 smallint, c2 integer, c3 bigint);
INSERT INTO createview_02725_schema.createview_02725_src VALUES (1, 100, 2000000);
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE VIEW。
-- primary-target-begin
CREATE VIEW createview_02725_schema.createview_02725_view AS SELECT c1, c2, c3 FROM createview_02725_schema.createview_02725_base WHERE c1 > 0;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS view_state FROM pg_catalog.pg_class WHERE relname = 'createview_02725_view' AND relkind = 'v' ORDER BY count(*);
MERGE INTO createview_02725_schema.createview_02725_view v USING createview_02725_schema.createview_02725_src s ON v.c1 = s.c1 WHEN MATCHED THEN UPDATE SET c2 = s.c2;
SELECT count(*) AS merge_effect FROM createview_02725_schema.createview_02725_base ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP VIEW createview_02725_schema.createview_02725_view CASCADE;
DROP VIEW IF EXISTS createview_02725_schema.createview_02725_refview CASCADE;
DROP SCHEMA IF EXISTS createview_02725_schema CASCADE;
DROP TABLE IF EXISTS createview_02725_schema.createview_02725_base, createview_02725_schema.createview_02725_join, createview_02725_schema.createview_02725_src CASCADE;
