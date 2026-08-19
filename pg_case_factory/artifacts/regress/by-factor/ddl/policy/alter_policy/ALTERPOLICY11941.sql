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
-- case_id: ALTERPOLICY11941
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/alter_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/alter_policy.yaml
-- primary_obligation_id: AP-EXT|11941|rename|catalog_query_pg_policy|drop_policy
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.alterpolicy_11941_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_11941_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和策略以及因子专用夹具。
CREATE ROLE alterpolicy_11941_owner LOGIN NOSUPERUSER;
CREATE TABLE public.alterpolicy_11941_tbl AS SELECT 1 AS c;
ALTER TABLE public.alterpolicy_11941_tbl OWNER TO alterpolicy_11941_owner;
ALTER TABLE public.alterpolicy_11941_tbl ENABLE ROW LEVEL SECURITY;
SET ROLE alterpolicy_11941_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信心的 ALTER POLICY。
-- primary-target-begin
ALTER POLICY alterpolicy_11941_no_such_policy ON public.alterpolicy_11941_tbl RENAME TO alterpolicy_11941_pol_new;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和行级安全策略行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS catalog_policy_absent FROM pg_catalog.pg_policy WHERE polname = 'alterpolicy_11941_no_such_policy' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP POLICY IF EXISTS alterpolicy_11941_pol ON public.alterpolicy_11941_tbl;
DROP TABLE IF EXISTS public.alterpolicy_11941_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_11941_owner;
DROP TABLE IF EXISTS public.alterpolicy_11941_tbl CASCADE;
