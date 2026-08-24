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
-- case_id: CREATEPOLICY00612
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/create_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/create_policy.yaml
-- primary_obligation_id: CPOL-EXT|00612|error_assertion|drop_table
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createpolicy_00612_t, createpolicy_00612_t2 CASCADE;
DROP TABLE IF EXISTS createpolicy_00612_nosuch CASCADE;
DROP TABLE IF EXISTS createpolicy_00612_src CASCADE;
DROP POLICY IF EXISTS createpolicy_00612_p ON createpolicy_00612_t;
DROP POLICY IF EXISTS createpolicy_00612_p ON createpolicy_00612_t2;
RESET ROLE;
DROP ROLE IF EXISTS createpolicy_00612_norole;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createpolicy_00612_t (id int, data text);
CREATE TABLE createpolicy_00612_t2 (id int, data text);
ALTER TABLE createpolicy_00612_t ENABLE ROW LEVEL SECURITY;
ALTER TABLE createpolicy_00612_t2 ENABLE ROW LEVEL SECURITY;
CREATE POLICY createpolicy_00612_p ON createpolicy_00612_t2 FOR ALL;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE POLICY。
-- primary-target-begin
CREATE POLICY createpolicy_00612_p ON createpolicy_00612_t AS RESTRICTIVE FOR ALL TO PUBLIC USING (true) WITH CHECK (true);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS createpolicy_00612_t2, createpolicy_00612_t CASCADE;
