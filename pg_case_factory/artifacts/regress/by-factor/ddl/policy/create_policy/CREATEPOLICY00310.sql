-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE POLICY object_state=exists_same_table
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEPOLICY00310
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/create_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/create_policy.yaml
-- primary_obligation_id: CPOL-EXT|00310|rls_behavior_test|drop_policy
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createpolicy_00310_t CASCADE;
DROP TABLE IF EXISTS createpolicy_00310_nosuch CASCADE;
DROP TABLE IF EXISTS createpolicy_00310_src CASCADE;
DROP POLICY IF EXISTS createpolicy_00310_p ON createpolicy_00310_t;
RESET ROLE;
DROP ROLE IF EXISTS createpolicy_00310_norole;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createpolicy_00310_t (id int, data text);
ALTER TABLE createpolicy_00310_t ENABLE ROW LEVEL SECURITY;
CREATE POLICY createpolicy_00310_p ON createpolicy_00310_t FOR ALL;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE POLICY。
-- primary-target-begin
CREATE POLICY createpolicy_00310_p ON createpolicy_00310_t AS PERMISSIVE FOR INSERT TO PUBLIC WITH CHECK (true);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) FROM createpolicy_00310_t ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP POLICY IF EXISTS createpolicy_00310_p ON createpolicy_00310_t;
DROP TABLE IF EXISTS createpolicy_00310_t CASCADE;
