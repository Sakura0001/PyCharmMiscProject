-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER RULE privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERRULE00428
-- source_md: skills/pg-sql-generation/references/statements/ddl/rule/alter_rule.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/rule/alter_rule.yaml
-- primary_obligation_id: AR-EXT|00428|error_assertion|drop_rule
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.alterrule_00428_host CASCADE;
DROP OWNED BY alterrule_00428_actor CASCADE;
DROP ROLE IF EXISTS alterrule_00428_actor;
DROP OWNED BY alterrule_00428_owner CASCADE;
DROP ROLE IF EXISTS alterrule_00428_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterrule_00428_owner LOGIN;
CREATE ROLE alterrule_00428_actor LOGIN NOSUPERUSER;
GRANT CREATE ON SCHEMA public TO alterrule_00428_owner;
GRANT USAGE ON SCHEMA public TO alterrule_00428_actor;
SET ROLE alterrule_00428_owner;
CREATE TABLE public.alterrule_00428_host (alterrule_00428_col integer);
CREATE RULE alterrule_00428_existing_rule AS ON INSERT TO public.alterrule_00428_host DO INSTEAD NOTHING;
RESET ROLE;
SET ROLE alterrule_00428_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER RULE。
-- primary-target-begin
ALTER RULE alterrule_00428_existing_rule ON public.alterrule_00428_host RENAME TO "alterrule_00428_Mixed Name";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP RULE IF EXISTS alterrule_00428_existing_rule ON public.alterrule_00428_host;
DROP OWNED BY alterrule_00428_actor CASCADE;
DROP ROLE IF EXISTS alterrule_00428_actor;
DROP OWNED BY alterrule_00428_owner CASCADE;
DROP ROLE IF EXISTS alterrule_00428_owner;
DROP TABLE IF EXISTS public.alterrule_00428_host CASCADE;
