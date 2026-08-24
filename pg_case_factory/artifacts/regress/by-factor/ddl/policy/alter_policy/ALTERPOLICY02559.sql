-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER POLICY policy_name_shape=nonexistent_name
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPOLICY02559
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/alter_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/alter_policy.yaml
-- primary_obligation_id: AP-EXT|02559|modify_roles|catalog_query_pg_policy|disable_rls_and_drop_policy
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterpolicy_02559_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_02559_owner;
DROP ROLE IF EXISTS alterpolicy_02559_role1;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和策略以及因子专用夹具。
CREATE ROLE alterpolicy_02559_owner LOGIN NOSUPERUSER;
CREATE ROLE alterpolicy_02559_role1 LOGIN;
CREATE TABLE alterpolicy_02559_tbl AS SELECT 1 AS c;
ALTER TABLE "alterpolicy_02559_tbl" OWNER TO alterpolicy_02559_owner;
SET ROLE alterpolicy_02559_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信心的 ALTER POLICY。
-- primary-target-begin
ALTER POLICY alterpolicy_02559_no_such_policy ON "alterpolicy_02559_tbl" TO alterpolicy_02559_role1;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和行级安全策略行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS catalog_policy_absent FROM pg_catalog.pg_policy WHERE polname = 'alterpolicy_02559_no_such_policy' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
ALTER TABLE IF EXISTS "alterpolicy_02559_tbl" DISABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS alterpolicy_02559_pol ON "alterpolicy_02559_tbl";
DROP TABLE IF EXISTS alterpolicy_02559_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_02559_owner;
DROP ROLE IF EXISTS alterpolicy_02559_role1;
DROP TABLE IF EXISTS alterpolicy_02559_tbl CASCADE;
