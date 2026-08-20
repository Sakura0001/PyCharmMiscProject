-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP POLICY object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPPOLICY01685
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/drop_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/drop_policy.yaml
-- primary_obligation_id: DROPPOLICY-EXT|01685|drop_policy|error_assertion|drop_table
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droppolicy_01685_t CASCADE;
DROP POLICY IF EXISTS droppolicy_01685_pol ON droppolicy_01685_t;
DROP POLICY IF EXISTS droppolicy_01685_pol2 ON droppolicy_01685_t;
DROP OWNED BY droppolicy_01685_owner;
DROP ROLE IF EXISTS droppolicy_01685_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地行级安全策略和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE ROLE droppolicy_01685_owner LOGIN NOSUPERUSER;
CREATE TABLE droppolicy_01685_t (c integer);
ALTER TABLE droppolicy_01685_t ENABLE ROW LEVEL SECURITY;
CREATE POLICY droppolicy_01685_pol ON droppolicy_01685_t FOR SELECT USING (true);
ALTER TABLE droppolicy_01685_t OWNER TO droppolicy_01685_owner;
SET ROLE droppolicy_01685_owner;
-- 3. 执行唯一获得覆盖信用的 DROP POLICY。
-- primary-target-begin
DROP POLICY droppolicy_01685_pol ON droppolicy_01685_t RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS policy_absent FROM pg_catalog.pg_policy WHERE polname = 'droppolicy_01685_pol' AND polrelid = (SELECT oid FROM pg_catalog.pg_class WHERE relname = 'droppolicy_01685_t') ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP POLICY IF EXISTS droppolicy_01685_pol ON droppolicy_01685_t;
DROP POLICY IF EXISTS droppolicy_01685_pol2 ON droppolicy_01685_t;
DROP OWNED BY droppolicy_01685_owner;
DROP ROLE IF EXISTS droppolicy_01685_owner;
DROP TABLE IF EXISTS droppolicy_01685_t CASCADE;
