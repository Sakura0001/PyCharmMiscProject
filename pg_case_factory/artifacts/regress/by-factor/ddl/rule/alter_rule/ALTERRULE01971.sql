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
-- case_id: ALTERRULE01971
-- source_md: skills/pg-sql-generation/references/statements/ddl/rule/alter_rule.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/rule/alter_rule.yaml
-- primary_obligation_id: AR-EXT|01971|error_assertion|revert_rename
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.alterrule_01971_host CASCADE;
DROP OWNED BY alterrule_01971_owner CASCADE;
DROP ROLE IF EXISTS alterrule_01971_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterrule_01971_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterrule_01971_owner;
SET ROLE alterrule_01971_owner;
CREATE TABLE public.alterrule_01971_host (alterrule_01971_col integer);
CREATE RULE alterrule_01971_rule AS ON INSERT TO public.alterrule_01971_host DO INSTEAD NOTHING;
CREATE RULE alterrule_01971_dup_rule AS ON INSERT TO public.alterrule_01971_host DO INSTEAD NOTHING;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER RULE。
-- primary-target-begin
ALTER RULE alterrule_01971_rule ON public.alterrule_01971_host RENAME TO alterrule_01971_dup_rule;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY alterrule_01971_owner CASCADE;
DROP ROLE IF EXISTS alterrule_01971_owner;
DROP TABLE IF EXISTS public.alterrule_01971_host CASCADE;
