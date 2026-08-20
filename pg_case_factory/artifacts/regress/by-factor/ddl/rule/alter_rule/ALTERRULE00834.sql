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
-- case_id: ALTERRULE00834
-- source_md: skills/pg-sql-generation/references/statements/ddl/rule/alter_rule.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/rule/alter_rule.yaml
-- primary_obligation_id: AR-EXT|00834|catalog_query_pg_rewrite|drop_table
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterrule_00834_host CASCADE;
DROP OWNED BY alterrule_00834_actor CASCADE;
DROP ROLE IF EXISTS alterrule_00834_actor;
DROP OWNED BY alterrule_00834_owner CASCADE;
DROP ROLE IF EXISTS alterrule_00834_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterrule_00834_owner LOGIN;
CREATE ROLE alterrule_00834_actor LOGIN NOSUPERUSER;
GRANT CREATE ON SCHEMA public TO alterrule_00834_owner;
GRANT USAGE ON SCHEMA public TO alterrule_00834_actor;
SET ROLE alterrule_00834_owner;
CREATE TABLE alterrule_00834_host (alterrule_00834_col integer);
CREATE RULE "alterrule_00834_Mixed Rule" AS ON INSERT TO "alterrule_00834_host" DO INSTEAD NOTHING;
RESET ROLE;
SET ROLE alterrule_00834_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER RULE。
-- primary-target-begin
ALTER RULE "alterrule_00834_Mixed Rule" ON "alterrule_00834_host" RENAME TO alterrule_00834_renamed;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS rule_renamed FROM pg_catalog.pg_rewrite AS r JOIN pg_catalog.pg_class AS c ON r.ev_class = c.oid WHERE r.rulename = 'alterrule_00834_renamed' AND c.relname = 'alterrule_00834_host' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY alterrule_00834_actor CASCADE;
DROP ROLE IF EXISTS alterrule_00834_actor;
DROP OWNED BY alterrule_00834_owner CASCADE;
DROP ROLE IF EXISTS alterrule_00834_owner;
DROP TABLE IF EXISTS alterrule_00834_host CASCADE;
