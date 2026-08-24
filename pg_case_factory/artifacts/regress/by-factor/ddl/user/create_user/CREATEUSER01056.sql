-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE USER object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEUSER01056
-- source_md: skills/pg-sql-generation/references/statements/ddl/user/create_user.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user/create_user.yaml
-- primary_obligation_id: CU-EXT|01056|catalog_query_pg_roles|revoke_membership
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS createuser_01056_user CASCADE;
DROP ROLE IF EXISTS createuser_01056_ref CASCADE;
DROP ROLE IF EXISTS createuser_01056_ref1 CASCADE;
DROP ROLE IF EXISTS createuser_01056_ref2 CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createuser_01056_user;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE USER。
-- primary-target-begin
CREATE USER createuser_01056_user WITH LOGIN, VALID UNTIL '2099-12-31 23:59:59';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS role_state FROM pg_catalog.pg_roles WHERE rolname = 'createuser_01056_user' ORDER BY count(*);
-- 5. 清理全部本编号对象。
REVOKE createuser_01056_ref FROM createuser_01056_user;
DROP OWNED BY createuser_01056_user CASCADE;
DROP ROLE IF EXISTS createuser_01056_user;
SELECT 1 AS residual_check_no_objects;
