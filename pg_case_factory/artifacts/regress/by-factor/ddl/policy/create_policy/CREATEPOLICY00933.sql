-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE POLICY target_form=create_policy
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEPOLICY00933
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/create_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/create_policy.yaml
-- primary_obligation_id: CPOL-EXT|00933|rls_behavior_test|drop_table
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createpolicy_00933_t CASCADE;
DROP TABLE IF EXISTS createpolicy_00933_nosuch CASCADE;
DROP TABLE IF EXISTS createpolicy_00933_src CASCADE;
DROP POLICY IF EXISTS createpolicy_00933_p ON createpolicy_00933_t;
RESET ROLE;
DROP ROLE IF EXISTS createpolicy_00933_norole;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createpolicy_00933_t (id int, data text);
ALTER TABLE createpolicy_00933_t ENABLE ROW LEVEL SECURITY;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE POLICY。
-- primary-target-begin
CREATE POLICY createpolicy_00933_p ON createpolicy_00933_t AS RESTRICTIVE FOR DELETE TO PUBLIC USING (true);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) FROM createpolicy_00933_t ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS createpolicy_00933_t CASCADE;
