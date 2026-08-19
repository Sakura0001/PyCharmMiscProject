-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER POLICY new_name_shape=simple_id
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPOLICY12779
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/alter_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/alter_policy.yaml
-- primary_obligation_id: AP-EXT|12779|rename|error_assertion|disable_rls_and_drop_policy
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterpolicy_12779_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_12779_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和策略以及因子专用夹具。
CREATE ROLE alterpolicy_12779_owner LOGIN NOSUPERUSER;
CREATE TABLE alterpolicy_12779_tbl AS SELECT 1 AS c;
ALTER TABLE alterpolicy_12779_tbl OWNER TO alterpolicy_12779_owner;
CREATE POLICY alterpolicy_12779_pol_ex ON alterpolicy_12779_tbl FOR ALL TO PUBLIC USING (false) WITH CHECK (false);
ALTER TABLE alterpolicy_12779_tbl ENABLE ROW LEVEL SECURITY;
SET ROLE alterpolicy_12779_owner;
-- 3. 执行唯一获得覆盖信心的 ALTER POLICY。
-- primary-target-begin
ALTER POLICY alterpolicy_12779_pol_ex ON alterpolicy_12779_tbl RENAME TO alterpolicy_12779_pol_new;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和行级安全策略行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
ALTER TABLE IF EXISTS alterpolicy_12779_tbl DISABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS alterpolicy_12779_pol_ex ON alterpolicy_12779_tbl;
DROP TABLE IF EXISTS alterpolicy_12779_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_12779_owner;
DROP TABLE IF EXISTS alterpolicy_12779_tbl CASCADE;
