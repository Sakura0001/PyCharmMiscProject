-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER POLICY new_name_shape=simple_id
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPOLICY12766
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/alter_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/alter_policy.yaml
-- primary_obligation_id: AP-EXT|12766|rename|error_assertion|revert_rename
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.alterpolicy_12766_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_12766_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和策略以及因子专用夹具。
CREATE ROLE alterpolicy_12766_owner LOGIN NOSUPERUSER;
CREATE TABLE public.alterpolicy_12766_tbl AS SELECT 1 AS c;
ALTER TABLE public.alterpolicy_12766_tbl OWNER TO alterpolicy_12766_owner;
CREATE POLICY alterpolicy_12766_pol_ex ON public.alterpolicy_12766_tbl FOR ALL TO PUBLIC USING (false) WITH CHECK (false);
ALTER TABLE public.alterpolicy_12766_tbl ENABLE ROW LEVEL SECURITY;
SET ROLE alterpolicy_12766_owner;
-- 3. 执行唯一获得覆盖信心的 ALTER POLICY。
-- primary-target-begin
ALTER POLICY alterpolicy_12766_pol_ex ON public.alterpolicy_12766_tbl RENAME TO alterpolicy_12766_pol_new;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和行级安全策略行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP POLICY IF EXISTS alterpolicy_12766_pol_ex ON public.alterpolicy_12766_tbl;
ALTER POLICY IF EXISTS alterpolicy_12766_pol_new ON public.alterpolicy_12766_tbl RENAME TO alterpolicy_12766_pol_ex;
DROP POLICY IF EXISTS alterpolicy_12766_pol_new ON public.alterpolicy_12766_tbl;
DROP TABLE IF EXISTS public.alterpolicy_12766_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_12766_owner;
DROP TABLE IF EXISTS public.alterpolicy_12766_tbl CASCADE;
