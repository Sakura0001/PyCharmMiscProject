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
-- case_id: CREATEVIEW01786
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/create_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/create_view.yaml
-- primary_obligation_id: CV-EXT|01786|error_assertion|drop_view_cascade|query_type
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createview_01786_schema.createview_01786_base, createview_01786_schema.createview_01786_join, createview_01786_schema.createview_01786_src CASCADE;
DROP VIEW IF EXISTS createview_01786_schema.createview_01786_view CASCADE;
DROP VIEW IF EXISTS createview_01786_schema.createview_01786_refview CASCADE;
DROP SCHEMA IF EXISTS createview_01786_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createview_01786_schema;
CREATE TABLE createview_01786_schema.createview_01786_base (c1 date, c2 timestamp, c3 interval);
INSERT INTO createview_01786_schema.createview_01786_base VALUES ('2026-01-01', '2026-01-01 12:00:00', '1 day');
CREATE TABLE createview_01786_schema.createview_01786_src (c1 date, c2 timestamp, c3 interval);
INSERT INTO createview_01786_schema.createview_01786_src VALUES ('2026-01-01', '2026-01-01 12:00:00', '1 day');
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE VIEW。
-- primary-target-begin
CREATE VIEW createview_01786_schema.createview_01786_view AS SELECT c1, c2, c3 FROM createview_01786_schema.createview_01786_base WHERE c1 > 0;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
MERGE INTO createview_01786_schema.createview_01786_view v USING createview_01786_schema.createview_01786_src s ON v.c1 = s.c1 WHEN MATCHED THEN UPDATE SET c2 = s.c2;
SELECT count(*) AS merge_effect FROM createview_01786_schema.createview_01786_base ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP VIEW createview_01786_schema.createview_01786_view CASCADE;
DROP VIEW IF EXISTS createview_01786_schema.createview_01786_refview CASCADE;
DROP SCHEMA IF EXISTS createview_01786_schema CASCADE;
DROP TABLE IF EXISTS createview_01786_schema.createview_01786_base, createview_01786_schema.createview_01786_join, createview_01786_schema.createview_01786_src CASCADE;
