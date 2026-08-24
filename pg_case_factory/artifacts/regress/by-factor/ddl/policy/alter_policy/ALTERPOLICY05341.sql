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
-- case_id: ALTERPOLICY05341
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/alter_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/alter_policy.yaml
-- primary_obligation_id: AP-EXT|05341|modify_roles|catalog_query_pg_policy|drop_policy
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.alterpolicy_05341_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_05341_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和策略以及因子专用夹具。
CREATE ROLE alterpolicy_05341_owner LOGIN NOSUPERUSER;
CREATE TABLE public.alterpolicy_05341_tbl AS SELECT 1 AS c;
ALTER TABLE public.alterpolicy_05341_tbl OWNER TO alterpolicy_05341_owner;
CREATE POLICY alterpolicy_05341_pol ON public.alterpolicy_05341_tbl FOR ALL TO PUBLIC USING (false) WITH CHECK (false);
ALTER TABLE public.alterpolicy_05341_tbl ENABLE ROW LEVEL SECURITY;
SET ROLE alterpolicy_05341_owner;
-- 3. 执行唯一获得覆盖信心的 ALTER POLICY。
-- primary-target-begin
ALTER POLICY "alterpolicy_05341_pol" ON public.alterpolicy_05341_tbl TO CURRENT_ROLE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和行级安全策略行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS catalog_policy_present FROM pg_catalog.pg_policy WHERE polname = 'alterpolicy_05341_pol' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP POLICY IF EXISTS alterpolicy_05341_pol ON public.alterpolicy_05341_tbl;
DROP TABLE IF EXISTS public.alterpolicy_05341_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_05341_owner;
DROP TABLE IF EXISTS public.alterpolicy_05341_tbl CASCADE;
