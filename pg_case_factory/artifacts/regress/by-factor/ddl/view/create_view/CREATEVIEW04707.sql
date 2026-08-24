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
-- case_id: CREATEVIEW04707
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/create_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/create_view.yaml
-- primary_obligation_id: CV-EXT|04707|information_schema_views|drop_view_if_exists|query_name
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createview_04707_schema.createview_04707_base, createview_04707_schema.createview_04707_join, createview_04707_schema.createview_04707_src CASCADE;
DROP VIEW IF EXISTS createview_04707_schema.createview_04707_view CASCADE;
DROP VIEW IF EXISTS createview_04707_schema.createview_04707_refview CASCADE;
DROP SCHEMA IF EXISTS createview_04707_schema CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createview_04707_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createview_04707_schema;
CREATE TABLE createview_04707_schema.createview_04707_base (c1 smallint, c2 integer, c3 bigint);
INSERT INTO createview_04707_schema.createview_04707_base VALUES (1, 100, 2000000);
CREATE TABLE createview_04707_schema.createview_04707_src (c1 smallint, c2 integer, c3 bigint);
INSERT INTO createview_04707_schema.createview_04707_src VALUES (1, 100, 2000000);
CREATE ROLE createview_04707_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA createview_04707_schema TO createview_04707_actor;
GRANT SELECT ON createview_04707_schema.createview_04707_base TO createview_04707_actor;
SET ROLE createview_04707_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE VIEW。
-- primary-target-begin
CREATE VIEW createview_04707_schema.createview_04707_view AS SELECT c1, c2, c3 FROM createview_04707_schema.createview_04707_base WHERE c1 > 0;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS view_state FROM information_schema.views WHERE table_name = 'createview_04707_view' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP VIEW IF EXISTS createview_04707_schema.createview_04707_view CASCADE;
DROP VIEW IF EXISTS createview_04707_schema.createview_04707_refview CASCADE;
DROP SCHEMA IF EXISTS createview_04707_schema CASCADE;
DROP OWNED BY createview_04707_actor CASCADE;
DROP ROLE IF EXISTS createview_04707_actor;
DROP TABLE IF EXISTS createview_04707_schema.createview_04707_base, createview_04707_schema.createview_04707_join, createview_04707_schema.createview_04707_src CASCADE;
