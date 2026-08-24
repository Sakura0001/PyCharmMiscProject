-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE USER privilege_level=non_createrole
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEUSER01019
-- source_md: skills/pg-sql-generation/references/statements/ddl/user/create_user.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user/create_user.yaml
-- primary_obligation_id: CU-EXT|01019|catalog_query_pg_roles|drop_role
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS createuser_01019_user CASCADE;
DROP ROLE IF EXISTS createuser_01019_ref CASCADE;
DROP ROLE IF EXISTS createuser_01019_ref1 CASCADE;
DROP ROLE IF EXISTS createuser_01019_ref2 CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createuser_01019_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createuser_01019_actor LOGIN NOSUPERUSER NOCREATEROLE;
CREATE ROLE createuser_01019_ref;
SET ROLE createuser_01019_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE USER。
-- primary-target-begin
CREATE USER createuser_01019_user WITH LOGIN, PASSWORD NULL, VALID UNTIL '2099-12-31 23:59:59', ADMIN createuser_01019_ref;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS role_state FROM pg_catalog.pg_roles WHERE rolname = 'createuser_01019_user' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS createuser_01019_user;
DROP ROLE IF EXISTS createuser_01019_ref;
DROP OWNED BY createuser_01019_actor CASCADE;
DROP ROLE IF EXISTS createuser_01019_actor;
SELECT 1 AS residual_check_no_objects;
