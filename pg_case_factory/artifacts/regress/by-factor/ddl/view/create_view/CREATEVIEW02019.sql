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
-- case_id: CREATEVIEW02019
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/create_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/create_view.yaml
-- primary_obligation_id: CV-EXT|02019|information_schema_views|drop_view_if_exists|query_type
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createview_02019_schema.createview_02019_base, createview_02019_schema.createview_02019_join, createview_02019_schema.createview_02019_src CASCADE;
DROP VIEW IF EXISTS createview_02019_schema.createview_02019_view CASCADE;
DROP VIEW IF EXISTS createview_02019_schema.createview_02019_refview CASCADE;
DROP SCHEMA IF EXISTS createview_02019_schema CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createview_02019_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createview_02019_schema;
CREATE TABLE createview_02019_schema.createview_02019_base (c1 json, c2 jsonb, c3 text);
INSERT INTO createview_02019_schema.createview_02019_base VALUES ('[1,2,3]', '[4,5,6]', 'jsonrow');
CREATE TABLE createview_02019_schema.createview_02019_join (c1 json, c2 jsonb, c3 text);
INSERT INTO createview_02019_schema.createview_02019_join VALUES ('[1,2,3]', '[4,5,6]', 'jsonrow');
CREATE ROLE createview_02019_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA createview_02019_schema TO createview_02019_actor;
GRANT SELECT ON createview_02019_schema.createview_02019_base TO createview_02019_actor;
SET ROLE createview_02019_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE VIEW。
-- primary-target-begin
CREATE VIEW createview_02019_schema.createview_02019_view AS SELECT a.c1, b.c2 FROM createview_02019_schema.createview_02019_base a JOIN createview_02019_schema.createview_02019_join b ON a.c1 = b.c1;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS view_state FROM information_schema.views WHERE table_name = 'createview_02019_view' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP VIEW IF EXISTS createview_02019_schema.createview_02019_view CASCADE;
DROP VIEW IF EXISTS createview_02019_schema.createview_02019_refview CASCADE;
DROP SCHEMA IF EXISTS createview_02019_schema CASCADE;
DROP OWNED BY createview_02019_actor CASCADE;
DROP ROLE IF EXISTS createview_02019_actor;
DROP TABLE IF EXISTS createview_02019_schema.createview_02019_base, createview_02019_schema.createview_02019_join, createview_02019_schema.createview_02019_src CASCADE;
