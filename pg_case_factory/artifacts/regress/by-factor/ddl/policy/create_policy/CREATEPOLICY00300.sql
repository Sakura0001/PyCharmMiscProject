-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE POLICY privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEPOLICY00300
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/create_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/create_policy.yaml
-- primary_obligation_id: CPOL-EXT|00300|catalog_query_pg_policy|drop_table
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createpolicy_00300_t CASCADE;
DROP TABLE IF EXISTS createpolicy_00300_nosuch CASCADE;
DROP TABLE IF EXISTS createpolicy_00300_src CASCADE;
DROP POLICY IF EXISTS createpolicy_00300_p ON createpolicy_00300_t;
RESET ROLE;
DROP OWNED BY createpolicy_00300_actor CASCADE;
DROP ROLE IF EXISTS createpolicy_00300_actor;
DROP ROLE IF EXISTS createpolicy_00300_norole;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createpolicy_00300_t (id int, data text);
ALTER TABLE createpolicy_00300_t ENABLE ROW LEVEL SECURITY;
CREATE ROLE createpolicy_00300_actor LOGIN NOSUPERUSER NOBYPASSRLS;
SET ROLE createpolicy_00300_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE POLICY。
-- primary-target-begin
CREATE POLICY createpolicy_00300_p ON createpolicy_00300_t AS PERMISSIVE FOR INSERT TO PUBLIC WITH CHECK (true);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS policy_state FROM pg_catalog.pg_policy WHERE polname = 'createpolicy_00300_p' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY createpolicy_00300_actor CASCADE;
DROP ROLE IF EXISTS createpolicy_00300_actor;
DROP TABLE IF EXISTS createpolicy_00300_t CASCADE;
