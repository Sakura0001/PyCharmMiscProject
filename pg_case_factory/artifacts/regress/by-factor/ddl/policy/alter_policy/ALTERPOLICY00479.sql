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
-- case_id: ALTERPOLICY00479
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/alter_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/alter_policy.yaml
-- primary_obligation_id: AP-EXT|00479|modify_combined|error_assertion|disable_rls_and_drop_policy
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.alterpolicy_00479_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_00479_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和策略以及因子专用夹具。
CREATE ROLE alterpolicy_00479_actor LOGIN NOSUPERUSER;
CREATE TABLE public.alterpolicy_00479_tbl AS SELECT 1 AS c;
CREATE POLICY alterpolicy_00479_pol ON public.alterpolicy_00479_tbl FOR ALL TO PUBLIC USING (false) WITH CHECK (false);
ALTER TABLE public.alterpolicy_00479_tbl ENABLE ROW LEVEL SECURITY;
SET ROLE alterpolicy_00479_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信心的 ALTER POLICY。
-- primary-target-begin
ALTER POLICY alterpolicy_00479_pol ON public.alterpolicy_00479_tbl TO PUBLIC USING (true) WITH CHECK (true);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和行级安全策略行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
ALTER TABLE IF EXISTS public.alterpolicy_00479_tbl DISABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS alterpolicy_00479_pol ON public.alterpolicy_00479_tbl;
DROP TABLE IF EXISTS public.alterpolicy_00479_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_00479_actor;
DROP TABLE IF EXISTS public.alterpolicy_00479_tbl CASCADE;
