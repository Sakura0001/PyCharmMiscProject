-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER USER database_name_shape=nonexistent_name
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERUSER03072
-- source_md: skills/pg-sql-generation/references/statements/ddl/user/alter_user.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user/alter_user.yaml
-- primary_obligation_id: AUSR-EXT|03072|error_assertion|revert_option
-- expected_outcome: expected_failure
-- expected_sqlstate: 3D000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS alteruser_03072_role;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alteruser_03072_role LOGIN;
SET ROLE alteruser_03072_role;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER USER。
-- primary-target-begin
ALTER USER alteruser_03072_role IN DATABASE alteruser_03072_nosuchdb SET work_mem = '4MB';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '3D000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS alteruser_03072_role;
