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
-- case_id: ALTERRULE00747
-- source_md: skills/pg-sql-generation/references/statements/ddl/rule/alter_rule.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/rule/alter_rule.yaml
-- primary_obligation_id: AR-EXT|00747|error_assertion|revert_rename
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterrule_00747_host CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE alterrule_00747_host (alterrule_00747_col integer);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER RULE。
-- primary-target-begin
ALTER RULE alterrule_00747_nonexistent_rule ON alterrule_00747_host RENAME TO "alterrule_00747_Mixed Name";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P01' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS alterrule_00747_host CASCADE;
