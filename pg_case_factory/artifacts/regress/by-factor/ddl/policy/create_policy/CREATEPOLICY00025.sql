-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE POLICY invalid_expression=window_function_in_expression
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEPOLICY00025
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/create_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/create_policy.yaml
-- primary_obligation_id: CPOL-SFV|sfv-81f8634a5ace676b8ff0f589|create_policy
-- expected_outcome: expected_failure
-- expected_sqlstate: 42803
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createpolicy_00025_t CASCADE;
DROP TABLE IF EXISTS createpolicy_00025_nosuch CASCADE;
DROP TABLE IF EXISTS createpolicy_00025_src CASCADE;
DROP POLICY IF EXISTS createpolicy_00025_p ON createpolicy_00025_t;
RESET ROLE;
DROP OWNED BY createpolicy_00025_role CASCADE;
DROP ROLE IF EXISTS createpolicy_00025_role;
DROP ROLE IF EXISTS createpolicy_00025_norole;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createpolicy_00025_t (id int, data text);
ALTER TABLE createpolicy_00025_t ENABLE ROW LEVEL SECURITY;
CREATE ROLE createpolicy_00025_role;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE POLICY。
-- primary-target-begin
CREATE POLICY createpolicy_00025_p ON createpolicy_00025_t AS PERMISSIVE FOR ALL TO createpolicy_00025_role USING (row_number() OVER () > 0);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42803' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS policy_state FROM pg_catalog.pg_policy WHERE polname = 'createpolicy_00025_p' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP POLICY IF EXISTS createpolicy_00025_p ON createpolicy_00025_t;
DROP OWNED BY createpolicy_00025_role CASCADE;
DROP ROLE IF EXISTS createpolicy_00025_role;
DROP TABLE IF EXISTS createpolicy_00025_t CASCADE;
