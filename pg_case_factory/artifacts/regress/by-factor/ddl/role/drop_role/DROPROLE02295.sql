-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP ROLE owned_objects=owns_multiple_objects
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPROLE02295
-- source_md: skills/pg-sql-generation/references/statements/ddl/role/drop_role.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/role/drop_role.yaml
-- primary_obligation_id: DROPROLE-EXT|02295|drop_role|effect_query|cascade_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droprole_02295_t CASCADE;
DROP FUNCTION IF EXISTS droprole_02295_fn();
DROP VIEW IF EXISTS droprole_02295_v;
DROP SEQUENCE IF EXISTS droprole_02295_seq;
DROP ROLE IF EXISTS droprole_02295_role;
DROP OWNED BY droprole_02295_actor;
DROP ROLE IF EXISTS droprole_02295_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE ROLE droprole_02295_actor CREATEROLE;
SELECT 1 AS target_role_intentionally_absent;
CREATE TABLE droprole_02295_t (c integer);
ALTER TABLE droprole_02295_t OWNER TO droprole_02295_role;
CREATE SEQUENCE droprole_02295_seq;
ALTER SEQUENCE droprole_02295_seq OWNER TO droprole_02295_role;
CREATE VIEW droprole_02295_v AS SELECT 1;
ALTER VIEW droprole_02295_v OWNER TO droprole_02295_role;
CREATE FUNCTION droprole_02295_fn() RETURNS integer AS 'SELECT 1' LANGUAGE sql;
ALTER FUNCTION droprole_02295_fn() OWNER TO droprole_02295_role;
SET ROLE droprole_02295_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP ROLE。
-- primary-target-begin
DROP ROLE IF EXISTS droprole_02295_role;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS role_absent FROM pg_catalog.pg_roles WHERE rolname = 'droprole_02295_role' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS droprole_02295_role;
DROP OWNED BY droprole_02295_actor;
DROP ROLE IF EXISTS droprole_02295_actor;
DROP FUNCTION IF EXISTS droprole_02295_fn();
DROP VIEW IF EXISTS droprole_02295_v;
DROP SEQUENCE IF EXISTS droprole_02295_seq;
DROP TABLE IF EXISTS droprole_02295_t CASCADE;
