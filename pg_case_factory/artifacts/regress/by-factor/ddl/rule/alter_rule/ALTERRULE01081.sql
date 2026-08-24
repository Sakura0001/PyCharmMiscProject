-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER RULE rule_name_shape=nonexistent_name
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERRULE01081
-- source_md: skills/pg-sql-generation/references/statements/ddl/rule/alter_rule.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/rule/alter_rule.yaml
-- primary_obligation_id: AR-EXT|01081|catalog_query_pg_rewrite|drop_view
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP VIEW IF EXISTS alterrule_01081_vhost CASCADE;
DROP OWNED BY alterrule_01081_owner CASCADE;
DROP ROLE IF EXISTS alterrule_01081_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterrule_01081_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterrule_01081_owner;
SET ROLE alterrule_01081_owner;
CREATE VIEW alterrule_01081_vhost AS SELECT 1 AS alterrule_01081_col;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER RULE。
-- primary-target-begin
ALTER RULE alterrule_01081_nonexistent_rule ON alterrule_01081_vhost RENAME TO alterrule_01081_renamed;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42P01' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS rule_absent FROM pg_catalog.pg_rewrite AS r JOIN pg_catalog.pg_class AS c ON r.ev_class = c.oid WHERE r.rulename = 'alterrule_01081_renamed' AND c.relname = 'alterrule_01081_vhost' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY alterrule_01081_owner CASCADE;
DROP ROLE IF EXISTS alterrule_01081_owner;
DROP VIEW IF EXISTS alterrule_01081_vhost CASCADE;
