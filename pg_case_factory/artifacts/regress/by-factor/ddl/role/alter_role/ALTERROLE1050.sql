-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER ROLE cross-factor extension: statement_branch=branch_4_set_from_current x verification_mode=effect_query x cleanup_mode=revert_attribute_change
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERROLE1050
-- source_md: skills/pg-sql-generation/references/statements/ddl/role/alter_role.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/role/alter_role.yaml
-- primary_obligation_id: ALTERROLE-EXT|1050|set_from_current|effect_query|revert_attribute_change
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS alterrole_1050_target;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE alterrole_1050_target LOGIN;
-- 3. 执行唯一获得覆盖信用的 ALTER ROLE。
-- primary-target-begin
ALTER ROLE alterrole_1050_target IN DATABASE alterrole_1050_nodb SET work_mem FROM CURRENT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT rolname FROM pg_catalog.pg_roles WHERE rolname = 'alterrole_1050_target' ORDER BY oid;
-- 5. 清理全部本编号对象。
DROP ROLE IF EXISTS alterrole_1050_target;
