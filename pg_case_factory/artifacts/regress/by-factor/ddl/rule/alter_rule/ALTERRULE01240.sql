-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER RULE rule_name_shape=quoted_id
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERRULE01240
-- source_md: skills/pg-sql-generation/references/statements/ddl/rule/alter_rule.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/rule/alter_rule.yaml
-- primary_obligation_id: AR-EXT|01240|catalog_query_pg_rewrite|drop_rule
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP VIEW IF EXISTS "alterrule_01240_vhost" CASCADE;
DROP OWNED BY alterrule_01240_owner CASCADE;
DROP ROLE IF EXISTS alterrule_01240_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterrule_01240_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterrule_01240_owner;
SET ROLE alterrule_01240_owner;
CREATE VIEW "alterrule_01240_vhost" AS SELECT 1 AS alterrule_01240_col;
CREATE RULE "alterrule_01240_Mixed Rule" AS ON INSERT TO "alterrule_01240_vhost" DO INSTEAD NOTHING;
-- 3. 执行唯一获得覆盖信用的 ALTER RULE。
-- primary-target-begin
ALTER RULE "alterrule_01240_Mixed Rule" ON "alterrule_01240_vhost" RENAME TO "alterrule_01240_Mixed Name";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS rule_renamed FROM pg_catalog.pg_rewrite AS r JOIN pg_catalog.pg_class AS c ON r.ev_class = c.oid WHERE r.rulename = 'alterrule_01240_Mixed Name' AND c.relname = 'alterrule_01240_vhost' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP RULE IF EXISTS "alterrule_01240_Mixed Name" ON "alterrule_01240_vhost";
DROP RULE IF EXISTS "alterrule_01240_Mixed Rule" ON "alterrule_01240_vhost";
DROP OWNED BY alterrule_01240_owner CASCADE;
DROP ROLE IF EXISTS alterrule_01240_owner;
DROP VIEW IF EXISTS "alterrule_01240_vhost" CASCADE;
