-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER POLICY privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPOLICY03704
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/alter_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/alter_policy.yaml
-- primary_obligation_id: AP-EXT|03704|modify_roles|rls_behavior_test|drop_table
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterpolicy_03704_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_03704_actor;
DROP ROLE IF EXISTS alterpolicy_03704_role1;
DROP ROLE IF EXISTS alterpolicy_03704_role2;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和策略以及因子专用夹具。
CREATE ROLE alterpolicy_03704_actor LOGIN NOSUPERUSER;
CREATE ROLE alterpolicy_03704_role1 LOGIN;
CREATE ROLE alterpolicy_03704_role2 LOGIN;
CREATE TABLE alterpolicy_03704_tbl AS SELECT 1 AS c;
CREATE POLICY alterpolicy_03704_pol ON alterpolicy_03704_tbl FOR ALL TO PUBLIC USING (false) WITH CHECK (false);
SET ROLE alterpolicy_03704_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信心的 ALTER POLICY。
-- primary-target-begin
ALTER POLICY alterpolicy_03704_pol ON alterpolicy_03704_tbl TO alterpolicy_03704_role1, alterpolicy_03704_role2;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和行级安全策略行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS rls_behavior_policy_present FROM pg_catalog.pg_policy WHERE polname = 'alterpolicy_03704_pol' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS alterpolicy_03704_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_03704_actor;
DROP ROLE IF EXISTS alterpolicy_03704_role1;
DROP ROLE IF EXISTS alterpolicy_03704_role2;
DROP TABLE IF EXISTS alterpolicy_03704_tbl CASCADE;
