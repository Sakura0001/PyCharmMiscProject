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
-- case_id: CREATEVIEW01246
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/create_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/create_view.yaml
-- primary_obligation_id: CV-EXT|01246|error_assertion|drop_view_cascade|name_shape
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createview_01246_schema.createview_01246_base, createview_01246_schema.createview_01246_join, createview_01246_schema.createview_01246_src CASCADE;
DROP VIEW IF EXISTS createview_01246_schema."createview_01246_view" CASCADE;
DROP VIEW IF EXISTS createview_01246_schema.createview_01246_refview CASCADE;
DROP SCHEMA IF EXISTS createview_01246_schema CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createview_01246_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createview_01246_schema;
CREATE TABLE createview_01246_schema.createview_01246_base (c1 smallint, c2 integer, c3 bigint);
INSERT INTO createview_01246_schema.createview_01246_base VALUES (1, 100, 2000000);
CREATE ROLE createview_01246_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA createview_01246_schema TO createview_01246_actor;
GRANT SELECT ON createview_01246_schema.createview_01246_base TO createview_01246_actor;
SET ROLE createview_01246_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE VIEW。
-- primary-target-begin
CREATE VIEW createview_01246_schema."createview_01246_view" AS SELECT c1, c2, c3 FROM createview_01246_schema.createview_01246_base;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP VIEW createview_01246_schema."createview_01246_view" CASCADE;
DROP VIEW IF EXISTS createview_01246_schema.createview_01246_refview CASCADE;
DROP SCHEMA IF EXISTS createview_01246_schema CASCADE;
DROP OWNED BY createview_01246_actor CASCADE;
DROP ROLE IF EXISTS createview_01246_actor;
DROP TABLE IF EXISTS createview_01246_schema.createview_01246_base, createview_01246_schema.createview_01246_join, createview_01246_schema.createview_01246_src CASCADE;
