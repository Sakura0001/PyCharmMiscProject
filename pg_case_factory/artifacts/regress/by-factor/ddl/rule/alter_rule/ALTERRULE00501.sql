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
-- case_id: ALTERRULE00501
-- source_md: skills/pg-sql-generation/references/statements/ddl/rule/alter_rule.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/rule/alter_rule.yaml
-- primary_obligation_id: AR-EXT|00501|error_assertion|drop_view
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP VIEW IF EXISTS alterrule_00501_vhost CASCADE;
DROP OWNED BY alterrule_00501_actor CASCADE;
DROP ROLE IF EXISTS alterrule_00501_actor;
DROP OWNED BY alterrule_00501_owner CASCADE;
DROP ROLE IF EXISTS alterrule_00501_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterrule_00501_owner LOGIN;
CREATE ROLE alterrule_00501_actor LOGIN NOSUPERUSER;
GRANT CREATE ON SCHEMA public TO alterrule_00501_owner;
GRANT USAGE ON SCHEMA public TO alterrule_00501_actor;
SET ROLE alterrule_00501_owner;
CREATE VIEW alterrule_00501_vhost AS SELECT 1 AS alterrule_00501_col;
CREATE RULE "alterrule_00501_Mixed Rule" AS ON INSERT TO alterrule_00501_vhost DO INSTEAD NOTHING;
RESET ROLE;
SET ROLE alterrule_00501_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER RULE。
-- primary-target-begin
ALTER RULE "alterrule_00501_Mixed Rule" ON alterrule_00501_vhost RENAME TO "alterrule_00501_Mixed Name";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY alterrule_00501_actor CASCADE;
DROP ROLE IF EXISTS alterrule_00501_actor;
DROP OWNED BY alterrule_00501_owner CASCADE;
DROP ROLE IF EXISTS alterrule_00501_owner;
DROP VIEW IF EXISTS alterrule_00501_vhost CASCADE;
