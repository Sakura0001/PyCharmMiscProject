-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER USER new_name_shape=duplicate_name
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERUSER01988
-- source_md: skills/pg-sql-generation/references/statements/ddl/user/alter_user.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user/alter_user.yaml
-- primary_obligation_id: AUSR-EXT|01988|config_parameter_query|revert_option
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS alteruser_01988_role;
DROP ROLE IF EXISTS alteruser_01988_conflict;
DROP ROLE IF EXISTS alteruser_01988_conflict;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alteruser_01988_role LOGIN;
CREATE ROLE alteruser_01988_conflict LOGIN;
SET ROLE alteruser_01988_role;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER USER。
-- primary-target-begin
ALTER USER alteruser_01988_role RENAME TO alteruser_01988_conflict;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS config_param_state FROM pg_catalog.pg_settings WHERE name = 'work_mem' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS alteruser_01988_role;
DROP ROLE IF EXISTS alteruser_01988_conflict;
DROP ROLE IF EXISTS alteruser_01988_conflict;
