-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER RULE new_name_shape=duplicate_name_same_table
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERRULE01831
-- source_md: skills/pg-sql-generation/references/statements/ddl/rule/alter_rule.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/rule/alter_rule.yaml
-- primary_obligation_id: AR-EXT|01831|catalog_query_pg_rewrite|revert_rename
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP VIEW IF EXISTS "alterrule_01831_vhost" CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE VIEW "alterrule_01831_vhost" AS SELECT 1 AS alterrule_01831_col;
CREATE RULE alterrule_01831_dup_rule AS ON INSERT TO "alterrule_01831_vhost" DO INSTEAD NOTHING;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER RULE。
-- primary-target-begin
ALTER RULE _RETURN ON "alterrule_01831_vhost" RENAME TO alterrule_01831_dup_rule;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS return_rule_renamed FROM pg_catalog.pg_rewrite AS r JOIN pg_catalog.pg_class AS c ON r.ev_class = c.oid WHERE r.rulename = '_RETURN' AND c.relname = 'alterrule_01831_vhost' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP VIEW IF EXISTS "alterrule_01831_vhost" CASCADE;
