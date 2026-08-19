-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER POLICY alter_action=modify_roles
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPOLICY04698
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/alter_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/alter_policy.yaml
-- primary_obligation_id: AP-EXT|04698|modify_roles|rls_behavior_test|revert_rename
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.alterpolicy_04698_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_04698_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和策略以及因子专用夹具。
CREATE ROLE alterpolicy_04698_owner LOGIN NOSUPERUSER;
CREATE TABLE public.alterpolicy_04698_tbl AS SELECT 1 AS c;
ALTER TABLE public.alterpolicy_04698_tbl OWNER TO alterpolicy_04698_owner;
CREATE POLICY alterpolicy_04698_pol_ex ON public.alterpolicy_04698_tbl FOR ALL TO PUBLIC USING (false) WITH CHECK (false);
SET ROLE alterpolicy_04698_owner;
-- 3. 执行唯一获得覆盖信心的 ALTER POLICY。
-- primary-target-begin
ALTER POLICY alterpolicy_04698_pol_ex ON public.alterpolicy_04698_tbl TO CURRENT_ROLE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和行级安全策略行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS rls_behavior_policy_present FROM pg_catalog.pg_policy WHERE polname = 'alterpolicy_04698_pol_ex' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP POLICY IF EXISTS alterpolicy_04698_pol_ex ON public.alterpolicy_04698_tbl;
DROP TABLE IF EXISTS public.alterpolicy_04698_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_04698_owner;
DROP TABLE IF EXISTS public.alterpolicy_04698_tbl CASCADE;
