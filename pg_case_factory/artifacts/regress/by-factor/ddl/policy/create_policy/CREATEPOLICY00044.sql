-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE POLICY privilege_level=superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEPOLICY00044
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/create_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/create_policy.yaml
-- primary_obligation_id: CPOL-SFV|sfv-4fa29011b2e9bddd561e837b|create_policy
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createpolicy_00044_t CASCADE;
DROP TABLE IF EXISTS createpolicy_00044_nosuch CASCADE;
DROP TABLE IF EXISTS createpolicy_00044_src CASCADE;
DROP POLICY IF EXISTS createpolicy_00044_p ON createpolicy_00044_t;
RESET ROLE;
DROP OWNED BY createpolicy_00044_role CASCADE;
DROP ROLE IF EXISTS createpolicy_00044_role;
DROP ROLE IF EXISTS createpolicy_00044_norole;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createpolicy_00044_t (id int, data text);
ALTER TABLE createpolicy_00044_t ENABLE ROW LEVEL SECURITY;
CREATE ROLE createpolicy_00044_role;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE POLICY。
-- primary-target-begin
CREATE POLICY createpolicy_00044_p ON createpolicy_00044_t AS PERMISSIVE FOR ALL TO createpolicy_00044_role USING (true) WITH CHECK (true);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS policy_state FROM pg_catalog.pg_policy WHERE polname = 'createpolicy_00044_p' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP POLICY IF EXISTS createpolicy_00044_p ON createpolicy_00044_t;
DROP OWNED BY createpolicy_00044_role CASCADE;
DROP ROLE IF EXISTS createpolicy_00044_role;
DROP TABLE IF EXISTS createpolicy_00044_t CASCADE;
