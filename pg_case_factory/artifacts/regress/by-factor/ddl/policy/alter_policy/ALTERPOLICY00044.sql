-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER POLICY role_existence=role_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPOLICY00044
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/alter_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/alter_policy.yaml
-- primary_obligation_id: AP-SFV|sfv-5170c6bff544fb12b6982f12|modify_roles
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterpolicy_00044_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_00044_role1;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和策略以及因子专用夹具。
CREATE ROLE alterpolicy_00044_role1 LOGIN;
CREATE TABLE alterpolicy_00044_tbl AS SELECT 1 AS c;
CREATE POLICY alterpolicy_00044_pol ON alterpolicy_00044_tbl FOR ALL TO PUBLIC USING (false) WITH CHECK (false);
ALTER TABLE alterpolicy_00044_tbl ENABLE ROW LEVEL SECURITY;
-- 3. 执行唯一获得覆盖信心的 ALTER POLICY。
-- primary-target-begin
ALTER POLICY alterpolicy_00044_pol ON alterpolicy_00044_tbl TO alterpolicy_00044_role1;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和行级安全策略行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS catalog_policy_present FROM pg_catalog.pg_policy WHERE polname = 'alterpolicy_00044_pol' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP POLICY IF EXISTS alterpolicy_00044_pol ON alterpolicy_00044_tbl;
DROP TABLE IF EXISTS alterpolicy_00044_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_00044_role1;
DROP TABLE IF EXISTS alterpolicy_00044_tbl CASCADE;
