-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE POLICY table_name_shape=nonexistent_table
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEPOLICY00067
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/create_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/create_policy.yaml
-- primary_obligation_id: CPOL-SFV|sfv-71205b6754f12dba1f257569|create_policy
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createpolicy_00067_t CASCADE;
DROP TABLE IF EXISTS createpolicy_00067_nosuch CASCADE;
DROP TABLE IF EXISTS createpolicy_00067_src CASCADE;
DROP POLICY IF EXISTS createpolicy_00067_p ON createpolicy_00067_t;
RESET ROLE;
DROP OWNED BY createpolicy_00067_role CASCADE;
DROP ROLE IF EXISTS createpolicy_00067_role;
DROP ROLE IF EXISTS createpolicy_00067_norole;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createpolicy_00067_t (id int, data text);
ALTER TABLE createpolicy_00067_t ENABLE ROW LEVEL SECURITY;
CREATE ROLE createpolicy_00067_role;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE POLICY。
-- primary-target-begin
CREATE POLICY createpolicy_00067_p ON createpolicy_00067_nosuch AS PERMISSIVE FOR ALL TO createpolicy_00067_role USING (true) WITH CHECK (true);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P01' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS policy_state FROM pg_catalog.pg_policy WHERE polname = 'createpolicy_00067_p' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP POLICY IF EXISTS createpolicy_00067_p ON createpolicy_00067_t;
DROP OWNED BY createpolicy_00067_role CASCADE;
DROP ROLE IF EXISTS createpolicy_00067_role;
DROP TABLE IF EXISTS createpolicy_00067_t CASCADE;
