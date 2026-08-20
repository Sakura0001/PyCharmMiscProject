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
-- case_id: DROPPOLICY00549
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/drop_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/drop_policy.yaml
-- primary_obligation_id: DROPPOLICY-EXT|00549|drop_policy|notice_assertion|role_cleanup
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droppolicy_00549_t CASCADE;
DROP POLICY IF EXISTS droppolicy_00549_pol ON droppolicy_00549_t;
DROP POLICY IF EXISTS droppolicy_00549_pol2 ON droppolicy_00549_t;
\set ON_ERROR_STOP on
-- 2. 创建完整本地行级安全策略和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE TABLE droppolicy_00549_t (c integer);
ALTER TABLE droppolicy_00549_t ENABLE ROW LEVEL SECURITY;
CREATE POLICY droppolicy_00549_pol ON droppolicy_00549_t FOR SELECT USING (true);
-- 3. 执行唯一获得覆盖信用的 DROP POLICY。
-- primary-target-begin
DROP POLICY IF EXISTS droppolicy_00549_pol ON droppolicy_00549_t CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS policy_absent FROM pg_catalog.pg_policy WHERE polname = 'droppolicy_00549_pol' AND polrelid = (SELECT oid FROM pg_catalog.pg_class WHERE relname = 'droppolicy_00549_t') ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP POLICY IF EXISTS droppolicy_00549_pol ON droppolicy_00549_t;
DROP POLICY IF EXISTS droppolicy_00549_pol2 ON droppolicy_00549_t;
DROP TABLE IF EXISTS droppolicy_00549_t CASCADE;
