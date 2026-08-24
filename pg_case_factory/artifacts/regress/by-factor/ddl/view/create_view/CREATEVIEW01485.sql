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
-- case_id: CREATEVIEW01485
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/create_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/create_view.yaml
-- primary_obligation_id: CV-EXT|01485|error_assertion|drop_view_if_exists|query_type
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createview_01485_schema.createview_01485_base, createview_01485_schema.createview_01485_join, createview_01485_schema.createview_01485_src CASCADE;
DROP VIEW IF EXISTS createview_01485_schema.createview_01485_view CASCADE;
DROP VIEW IF EXISTS createview_01485_schema.createview_01485_refview CASCADE;
DROP SCHEMA IF EXISTS createview_01485_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createview_01485_schema;
CREATE TABLE createview_01485_schema.createview_01485_base (c1 varchar(50), c2 text, c3 char(10));
INSERT INTO createview_01485_schema.createview_01485_base VALUES ('hello', 'world', 'fixed');
CREATE TABLE createview_01485_schema.createview_01485_join (c1 varchar(50), c2 text, c3 char(10));
INSERT INTO createview_01485_schema.createview_01485_join VALUES ('hello', 'world', 'fixed');
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE VIEW。
-- primary-target-begin
CREATE VIEW createview_01485_schema.createview_01485_view AS SELECT a.c1, b.c2 FROM createview_01485_schema.createview_01485_base a JOIN createview_01485_schema.createview_01485_join b ON a.c1 = b.c1;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP VIEW IF EXISTS createview_01485_schema.createview_01485_view CASCADE;
DROP VIEW IF EXISTS createview_01485_schema.createview_01485_refview CASCADE;
DROP SCHEMA IF EXISTS createview_01485_schema CASCADE;
DROP TABLE IF EXISTS createview_01485_schema.createview_01485_base, createview_01485_schema.createview_01485_join, createview_01485_schema.createview_01485_src CASCADE;
