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
-- case_id: CREATEVIEW01799
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/create_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/create_view.yaml
-- primary_obligation_id: CV-EXT|01799|error_assertion|drop_base_table_cascade|query_type
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createview_01799_schema.createview_01799_base, createview_01799_schema.createview_01799_join, createview_01799_schema.createview_01799_src CASCADE;
DROP VIEW IF EXISTS createview_01799_schema.createview_01799_view CASCADE;
DROP VIEW IF EXISTS createview_01799_schema.createview_01799_refview CASCADE;
DROP SCHEMA IF EXISTS createview_01799_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createview_01799_schema;
CREATE TABLE createview_01799_schema.createview_01799_base (c1 numeric(10,2), c2 real, c3 double precision);
INSERT INTO createview_01799_schema.createview_01799_base VALUES (3.14, 2.5, 1.5);
CREATE TABLE createview_01799_schema.createview_01799_src (c1 numeric(10,2), c2 real, c3 double precision);
INSERT INTO createview_01799_schema.createview_01799_src VALUES (3.14, 2.5, 1.5);
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE VIEW。
-- primary-target-begin
CREATE VIEW createview_01799_schema.createview_01799_view AS SELECT c1, c2, c3 FROM createview_01799_schema.createview_01799_base WHERE c1 > 0;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
MERGE INTO createview_01799_schema.createview_01799_view v USING createview_01799_schema.createview_01799_src s ON v.c1 = s.c1 WHEN MATCHED THEN UPDATE SET c2 = s.c2;
SELECT count(*) AS merge_effect FROM createview_01799_schema.createview_01799_base ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP VIEW IF EXISTS createview_01799_schema.createview_01799_view CASCADE;
DROP TABLE IF EXISTS createview_01799_schema.createview_01799_base CASCADE;
DROP VIEW IF EXISTS createview_01799_schema.createview_01799_refview CASCADE;
DROP SCHEMA IF EXISTS createview_01799_schema CASCADE;
DROP TABLE IF EXISTS createview_01799_schema.createview_01799_base, createview_01799_schema.createview_01799_join, createview_01799_schema.createview_01799_src CASCADE;
