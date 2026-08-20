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
-- case_id: ALTERRULE00433
-- source_md: skills/pg-sql-generation/references/statements/ddl/rule/alter_rule.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/rule/alter_rule.yaml
-- primary_obligation_id: AR-EXT|00433|catalog_query_pg_rewrite|drop_view
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP VIEW IF EXISTS public.alterrule_00433_vhost CASCADE;
DROP OWNED BY alterrule_00433_actor CASCADE;
DROP ROLE IF EXISTS alterrule_00433_actor;
DROP OWNED BY alterrule_00433_owner CASCADE;
DROP ROLE IF EXISTS alterrule_00433_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterrule_00433_owner LOGIN;
CREATE ROLE alterrule_00433_actor LOGIN NOSUPERUSER;
GRANT CREATE ON SCHEMA public TO alterrule_00433_owner;
GRANT USAGE ON SCHEMA public TO alterrule_00433_actor;
SET ROLE alterrule_00433_owner;
CREATE VIEW public.alterrule_00433_vhost AS SELECT 1 AS alterrule_00433_col;
CREATE RULE alterrule_00433_existing_rule AS ON INSERT TO public.alterrule_00433_vhost DO INSTEAD NOTHING;
RESET ROLE;
SET ROLE alterrule_00433_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER RULE。
-- primary-target-begin
ALTER RULE alterrule_00433_existing_rule ON public.alterrule_00433_vhost RENAME TO "alterrule_00433_Mixed Name";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS rule_renamed FROM pg_catalog.pg_rewrite AS r JOIN pg_catalog.pg_class AS c ON r.ev_class = c.oid WHERE r.rulename = 'alterrule_00433_Mixed Name' AND c.relname = 'alterrule_00433_vhost' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY alterrule_00433_actor CASCADE;
DROP ROLE IF EXISTS alterrule_00433_actor;
DROP OWNED BY alterrule_00433_owner CASCADE;
DROP ROLE IF EXISTS alterrule_00433_owner;
DROP VIEW IF EXISTS public.alterrule_00433_vhost CASCADE;
