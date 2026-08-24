-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER POLICY alter_action=modify_using
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPOLICY08395
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/alter_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/alter_policy.yaml
-- primary_obligation_id: AP-EXT|08395|modify_using|rls_behavior_test|disable_rls_and_drop_policy
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.alterpolicy_08395_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_08395_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和策略以及因子专用夹具。
CREATE ROLE alterpolicy_08395_owner LOGIN NOSUPERUSER;
CREATE TABLE public.alterpolicy_08395_tbl AS SELECT 1 AS c;
ALTER TABLE public.alterpolicy_08395_tbl OWNER TO alterpolicy_08395_owner;
CREATE POLICY alterpolicy_08395_pol ON public.alterpolicy_08395_tbl FOR ALL TO PUBLIC USING (false) WITH CHECK (false);
ALTER TABLE public.alterpolicy_08395_tbl ENABLE ROW LEVEL SECURITY;
SET ROLE alterpolicy_08395_owner;
-- 3. 执行唯一获得覆盖信心的 ALTER POLICY。
-- primary-target-begin
ALTER POLICY alterpolicy_08395_pol ON public.alterpolicy_08395_tbl USING (false);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和行级安全策略行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS rls_behavior_policy_present FROM pg_catalog.pg_policy WHERE polname = 'alterpolicy_08395_pol' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
ALTER TABLE IF EXISTS public.alterpolicy_08395_tbl DISABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS alterpolicy_08395_pol ON public.alterpolicy_08395_tbl;
DROP TABLE IF EXISTS public.alterpolicy_08395_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_08395_owner;
DROP TABLE IF EXISTS public.alterpolicy_08395_tbl CASCADE;
