-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE ROLE role_identity=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEROLE01490
-- source_md: skills/pg-sql-generation/references/statements/ddl/role/create_role.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/role/create_role.yaml
-- primary_obligation_id: CRP-EXT|01490|membership_check_query|revoke_membership_then_drop
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS createrole_01490_role CASCADE;
DROP ROLE IF EXISTS createrole_01490_ref CASCADE;
DROP ROLE IF EXISTS createrole_01490_ref1 CASCADE;
DROP ROLE IF EXISTS createrole_01490_ref2 CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createrole_01490_role;
CREATE ROLE createrole_01490_ref;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE ROLE。
-- primary-target-begin
CREATE ROLE createrole_01490_role CONNECTION LIMIT 10, IN ROLE createrole_01490_ref;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS member_state FROM pg_catalog.pg_roles WHERE rolname = 'createrole_01490_role' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP OWNED BY createrole_01490_role CASCADE;
DROP ROLE IF EXISTS createrole_01490_role;
DROP ROLE IF EXISTS createrole_01490_ref;
SELECT 1 AS residual_check_no_objects;
