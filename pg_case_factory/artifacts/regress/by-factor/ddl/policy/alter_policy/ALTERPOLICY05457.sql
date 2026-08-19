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
-- case_id: ALTERPOLICY05457
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/alter_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/alter_policy.yaml
-- primary_obligation_id: AP-EXT|05457|modify_roles|error_assertion|drop_policy
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.alterpolicy_05457_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_05457_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和策略以及因子专用夹具。
CREATE ROLE alterpolicy_05457_owner LOGIN NOSUPERUSER;
CREATE TABLE public.alterpolicy_05457_tbl AS SELECT 1 AS c;
ALTER TABLE public.alterpolicy_05457_tbl OWNER TO alterpolicy_05457_owner;
CREATE POLICY alterpolicy_05457_pol ON public.alterpolicy_05457_tbl FOR ALL TO PUBLIC USING (false) WITH CHECK (false);
ALTER TABLE public.alterpolicy_05457_tbl ENABLE ROW LEVEL SECURITY;
SET ROLE alterpolicy_05457_owner;
-- 3. 执行唯一获得覆盖信心的 ALTER POLICY。
-- primary-target-begin
ALTER POLICY "alterpolicy_05457_pol" ON public.alterpolicy_05457_tbl TO SESSION_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和行级安全策略行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP POLICY IF EXISTS alterpolicy_05457_pol ON public.alterpolicy_05457_tbl;
DROP TABLE IF EXISTS public.alterpolicy_05457_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_05457_owner;
DROP TABLE IF EXISTS public.alterpolicy_05457_tbl CASCADE;
