-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP POLICY privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPPOLICY01643
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/drop_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/drop_policy.yaml
-- primary_obligation_id: DROPPOLICY-EXT|01643|drop_policy|rls_behavior_test|drop_table
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droppolicy_01643_t CASCADE;
DROP POLICY IF EXISTS droppolicy_01643_pol ON droppolicy_01643_t;
DROP POLICY IF EXISTS droppolicy_01643_pol2 ON droppolicy_01643_t;
DROP OWNED BY droppolicy_01643_actor;
DROP ROLE IF EXISTS droppolicy_01643_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地行级安全策略和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE ROLE droppolicy_01643_actor LOGIN NOSUPERUSER;
CREATE TABLE droppolicy_01643_t (c integer);
ALTER TABLE droppolicy_01643_t ENABLE ROW LEVEL SECURITY;
CREATE POLICY droppolicy_01643_pol ON droppolicy_01643_t FOR SELECT USING (true);
CREATE POLICY droppolicy_01643_pol2 ON droppolicy_01643_t FOR SELECT USING (true);
SET ROLE droppolicy_01643_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP POLICY。
-- primary-target-begin
DROP POLICY IF EXISTS droppolicy_01643_pol ON droppolicy_01643_t RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS policy_present FROM pg_catalog.pg_policy WHERE polname = 'droppolicy_01643_pol' AND polrelid = (SELECT oid FROM pg_catalog.pg_class WHERE relname = 'droppolicy_01643_t') ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP POLICY IF EXISTS droppolicy_01643_pol ON droppolicy_01643_t;
DROP POLICY IF EXISTS droppolicy_01643_pol2 ON droppolicy_01643_t;
DROP OWNED BY droppolicy_01643_actor;
DROP ROLE IF EXISTS droppolicy_01643_actor;
DROP TABLE IF EXISTS droppolicy_01643_t CASCADE;
