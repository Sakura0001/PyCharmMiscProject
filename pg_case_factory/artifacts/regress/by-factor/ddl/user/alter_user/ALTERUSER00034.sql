-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER USER new_name_shape=simple_id
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERUSER00034
-- source_md: skills/pg-sql-generation/references/statements/ddl/user/alter_user.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user/alter_user.yaml
-- primary_obligation_id: AUSR-SFV|sfv-61435d934064351068d12d8c|rename
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS alteruser_00034_role;
DROP ROLE IF EXISTS alteruser_00034_newrole;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alteruser_00034_role LOGIN;
-- 3. 执行唯一获得覆盖信用的 ALTER USER。
-- primary-target-begin
ALTER USER alteruser_00034_role RENAME TO alteruser_00034_newrole;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS role_state FROM pg_catalog.pg_roles WHERE rolname = 'alteruser_00034_newrole' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP ROLE IF EXISTS alteruser_00034_role;
DROP ROLE IF EXISTS alteruser_00034_newrole;
