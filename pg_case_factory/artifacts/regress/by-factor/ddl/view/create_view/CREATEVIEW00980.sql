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
-- case_id: CREATEVIEW00980
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/create_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/create_view.yaml
-- primary_obligation_id: CV-EXT|00980|select_from_view|drop_base_table_cascade|with_check
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createview_00980_schema.createview_00980_base, createview_00980_schema.createview_00980_join, createview_00980_schema.createview_00980_src CASCADE;
DROP VIEW IF EXISTS createview_00980_schema.createview_00980_view CASCADE;
DROP VIEW IF EXISTS createview_00980_schema.createview_00980_refview CASCADE;
DROP SCHEMA IF EXISTS createview_00980_schema CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createview_00980_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createview_00980_schema;
CREATE TABLE createview_00980_schema.createview_00980_base (c1 smallint, c2 integer, c3 bigint);
INSERT INTO createview_00980_schema.createview_00980_base VALUES (1, 100, 2000000);
CREATE ROLE createview_00980_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA createview_00980_schema TO createview_00980_actor;
GRANT SELECT ON createview_00980_schema.createview_00980_base TO createview_00980_actor;
SET ROLE createview_00980_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE VIEW。
-- primary-target-begin
CREATE VIEW createview_00980_schema.createview_00980_view WITH (check_option = cascaded) AS SELECT c1, c2, c3 FROM createview_00980_schema.createview_00980_base WITH CASCADED CHECK OPTION;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP VIEW IF EXISTS createview_00980_schema.createview_00980_view CASCADE;
DROP TABLE IF EXISTS createview_00980_schema.createview_00980_base CASCADE;
DROP VIEW IF EXISTS createview_00980_schema.createview_00980_refview CASCADE;
DROP SCHEMA IF EXISTS createview_00980_schema CASCADE;
DROP OWNED BY createview_00980_actor CASCADE;
DROP ROLE IF EXISTS createview_00980_actor;
DROP TABLE IF EXISTS createview_00980_schema.createview_00980_base, createview_00980_schema.createview_00980_join, createview_00980_schema.createview_00980_src CASCADE;
