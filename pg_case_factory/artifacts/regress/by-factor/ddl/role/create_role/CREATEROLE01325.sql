-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE ROLE executor_privilege=normal_user_no_createrole
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEROLE01325
-- source_md: skills/pg-sql-generation/references/statements/ddl/role/create_role.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/role/create_role.yaml
-- primary_obligation_id: CRP-EXT|01325|error_assertion|revoke_membership_then_drop
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS createrole_01325_role CASCADE;
DROP ROLE IF EXISTS createrole_01325_ref CASCADE;
DROP ROLE IF EXISTS createrole_01325_ref1 CASCADE;
DROP ROLE IF EXISTS createrole_01325_ref2 CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createrole_01325_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createrole_01325_actor LOGIN NOSUPERUSER NOCREATEROLE;
CREATE ROLE createrole_01325_ref;
SET ROLE createrole_01325_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE ROLE。
-- primary-target-begin
CREATE ROLE createrole_01325_role WITH PASSWORD NULL, CONNECTION LIMIT 10, IN ROLE createrole_01325_ref;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY createrole_01325_role CASCADE;
DROP ROLE IF EXISTS createrole_01325_role;
DROP ROLE IF EXISTS createrole_01325_ref;
DROP OWNED BY createrole_01325_actor CASCADE;
DROP ROLE IF EXISTS createrole_01325_actor;
SELECT 1 AS residual_check_no_objects;
