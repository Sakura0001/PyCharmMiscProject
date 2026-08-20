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
-- case_id: ALTERRULE00821
-- source_md: skills/pg-sql-generation/references/statements/ddl/rule/alter_rule.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/rule/alter_rule.yaml
-- primary_obligation_id: AR-EXT|00821|error_assertion|drop_view
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterrule_00821_host CASCADE;
DROP OWNED BY alterrule_00821_actor CASCADE;
DROP ROLE IF EXISTS alterrule_00821_actor;
DROP OWNED BY alterrule_00821_owner CASCADE;
DROP ROLE IF EXISTS alterrule_00821_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterrule_00821_owner LOGIN;
CREATE ROLE alterrule_00821_actor LOGIN NOSUPERUSER;
GRANT CREATE ON SCHEMA public TO alterrule_00821_owner;
GRANT USAGE ON SCHEMA public TO alterrule_00821_actor;
SET ROLE alterrule_00821_owner;
CREATE TABLE alterrule_00821_host (alterrule_00821_col integer);
CREATE RULE alterrule_00821_existing_rule AS ON INSERT TO alterrule_00821_host DO INSTEAD NOTHING;
RESET ROLE;
SET ROLE alterrule_00821_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER RULE。
-- primary-target-begin
ALTER RULE alterrule_00821_existing_rule ON alterrule_00821_host RENAME TO alterrule_00821_renamed;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY alterrule_00821_actor CASCADE;
DROP ROLE IF EXISTS alterrule_00821_actor;
DROP OWNED BY alterrule_00821_owner CASCADE;
DROP ROLE IF EXISTS alterrule_00821_owner;
DROP TABLE IF EXISTS alterrule_00821_host CASCADE;
