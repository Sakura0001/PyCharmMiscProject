-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE VIEW privilege_level=non_owner_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEVIEW04649
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/create_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/create_view.yaml
-- primary_obligation_id: CV-EXT|04649|information_schema_views|drop_base_table_cascade|query_name
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createview_04649_schema.createview_04649_base, createview_04649_schema.createview_04649_join, createview_04649_schema.createview_04649_src CASCADE;
DROP VIEW IF EXISTS createview_04649_schema.createview_04649_view CASCADE;
DROP VIEW IF EXISTS createview_04649_schema.createview_04649_refview CASCADE;
DROP SCHEMA IF EXISTS createview_04649_schema CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createview_04649_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createview_04649_schema;
CREATE TABLE createview_04649_schema.createview_04649_base (c1 smallint, c2 integer, c3 bigint);
INSERT INTO createview_04649_schema.createview_04649_base VALUES (1, 100, 2000000);
CREATE ROLE createview_04649_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA createview_04649_schema TO createview_04649_actor;
GRANT SELECT ON createview_04649_schema.createview_04649_base TO createview_04649_actor;
SET ROLE createview_04649_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE VIEW。
-- primary-target-begin
CREATE VIEW createview_04649_schema.createview_04649_view AS VALUES (1, 100), (1, 100);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS view_state FROM information_schema.views WHERE table_name = 'createview_04649_view' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP VIEW IF EXISTS createview_04649_schema.createview_04649_view CASCADE;
DROP TABLE IF EXISTS createview_04649_schema.createview_04649_base CASCADE;
DROP VIEW IF EXISTS createview_04649_schema.createview_04649_refview CASCADE;
DROP SCHEMA IF EXISTS createview_04649_schema CASCADE;
DROP OWNED BY createview_04649_actor CASCADE;
DROP ROLE IF EXISTS createview_04649_actor;
DROP TABLE IF EXISTS createview_04649_schema.createview_04649_base, createview_04649_schema.createview_04649_join, createview_04649_schema.createview_04649_src CASCADE;
