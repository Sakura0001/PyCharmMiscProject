-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE POLICY expression_compatibility=delete_with_check_incompatible
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEPOLICY00539
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/create_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/create_policy.yaml
-- primary_obligation_id: CPOL-EXT|00539|error_assertion|disable_rls_and_drop_policy
-- expected_outcome: expected_failure
-- expected_sqlstate: 42601
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createpolicy_00539_t, createpolicy_00539_t2 CASCADE;
DROP TABLE IF EXISTS createpolicy_00539_nosuch CASCADE;
DROP TABLE IF EXISTS createpolicy_00539_src CASCADE;
DROP POLICY IF EXISTS createpolicy_00539_p ON createpolicy_00539_t;
DROP POLICY IF EXISTS createpolicy_00539_p ON createpolicy_00539_t2;
RESET ROLE;
DROP ROLE IF EXISTS createpolicy_00539_norole;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createpolicy_00539_t (id int, data text);
CREATE TABLE createpolicy_00539_t2 (id int, data text);
ALTER TABLE createpolicy_00539_t ENABLE ROW LEVEL SECURITY;
ALTER TABLE createpolicy_00539_t2 ENABLE ROW LEVEL SECURITY;
CREATE POLICY createpolicy_00539_p ON createpolicy_00539_t2 FOR ALL;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE POLICY。
-- primary-target-begin
CREATE POLICY createpolicy_00539_p ON createpolicy_00539_t AS PERMISSIVE FOR DELETE TO PUBLIC USING (true) WITH CHECK (true);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42601' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP POLICY IF EXISTS createpolicy_00539_p ON createpolicy_00539_t;
DROP POLICY IF EXISTS createpolicy_00539_p ON createpolicy_00539_t2;
ALTER TABLE createpolicy_00539_t DISABLE ROW LEVEL SECURITY;
ALTER TABLE createpolicy_00539_t2 DISABLE ROW LEVEL SECURITY;
DROP TABLE IF EXISTS createpolicy_00539_t2, createpolicy_00539_t CASCADE;
