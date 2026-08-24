-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER RULE transaction_outcome=rollback
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERRULE00046
-- source_md: skills/pg-sql-generation/references/statements/ddl/rule/alter_rule.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/rule/alter_rule.yaml
-- primary_obligation_id: AR-RISK|transaction|rollback
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterrule_00046_host CASCADE;
DROP OWNED BY alterrule_00046_owner CASCADE;
DROP ROLE IF EXISTS alterrule_00046_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterrule_00046_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterrule_00046_owner;
SET ROLE alterrule_00046_owner;
CREATE TABLE alterrule_00046_host (alterrule_00046_col integer);
CREATE RULE alterrule_00046_rule AS ON INSERT TO alterrule_00046_host DO INSTEAD NOTHING;
BEGIN;
-- 3. 执行唯一获得覆盖信用的 ALTER RULE。
-- primary-target-begin
ALTER RULE alterrule_00046_rule ON alterrule_00046_host RENAME TO alterrule_00046_renamed;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
ROLLBACK;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS rule_renamed FROM pg_catalog.pg_rewrite AS r JOIN pg_catalog.pg_class AS c ON r.ev_class = c.oid WHERE r.rulename = 'alterrule_00046_renamed' AND c.relname = 'alterrule_00046_host' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
ALTER RULE alterrule_00046_renamed ON alterrule_00046_host RENAME TO alterrule_00046_rule;
DROP OWNED BY alterrule_00046_owner CASCADE;
DROP ROLE IF EXISTS alterrule_00046_owner;
DROP TABLE IF EXISTS alterrule_00046_host CASCADE;
