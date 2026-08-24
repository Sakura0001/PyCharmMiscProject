-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER POLICY new_name_shape=duplicate_name
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPOLICY10790
-- source_md: skills/pg-sql-generation/references/statements/ddl/policy/alter_policy.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/policy/alter_policy.yaml
-- primary_obligation_id: AP-EXT|10790|rename|catalog_query_pg_policy|revert_rename
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterpolicy_10790_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_10790_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和策略以及因子专用夹具。
CREATE ROLE alterpolicy_10790_owner LOGIN NOSUPERUSER;
CREATE TABLE alterpolicy_10790_tbl AS SELECT 1 AS c;
ALTER TABLE alterpolicy_10790_tbl OWNER TO alterpolicy_10790_owner;
CREATE POLICY alterpolicy_10790_pol ON alterpolicy_10790_tbl FOR ALL TO PUBLIC USING (false) WITH CHECK (false);
CREATE POLICY alterpolicy_10790_pol_dup ON alterpolicy_10790_tbl FOR ALL TO PUBLIC USING (false) WITH CHECK (false);
SET ROLE alterpolicy_10790_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信心的 ALTER POLICY。
-- primary-target-begin
ALTER POLICY alterpolicy_10790_pol ON alterpolicy_10790_tbl RENAME TO alterpolicy_10790_pol_dup;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和行级安全策略行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS catalog_policy_present FROM pg_catalog.pg_policy WHERE polname = 'alterpolicy_10790_pol' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP POLICY IF EXISTS alterpolicy_10790_pol ON alterpolicy_10790_tbl;
DROP POLICY IF EXISTS alterpolicy_10790_pol_dup ON alterpolicy_10790_tbl;
DROP TABLE IF EXISTS alterpolicy_10790_tbl CASCADE;
DROP ROLE IF EXISTS alterpolicy_10790_owner;
DROP TABLE IF EXISTS alterpolicy_10790_tbl CASCADE;
