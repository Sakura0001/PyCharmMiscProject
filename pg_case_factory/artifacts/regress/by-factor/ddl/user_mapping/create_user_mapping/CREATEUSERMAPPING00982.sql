-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE USER MAPPING server_name_shape=nonexistent_name
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEUSERMAPPING00982
-- source_md: skills/pg-sql-generation/references/statements/ddl/user_mapping/create_user_mapping.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user_mapping/create_user_mapping.yaml
-- primary_obligation_id: CUM-EXT|00982|error_assertion|drop_fdw|full_cross
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FOREIGN DATA WRAPPER IF EXISTS createusermapping_00982_fdw CASCADE;
DROP SCHEMA IF EXISTS createusermapping_00982_schema CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createusermapping_00982_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createusermapping_00982_schema;
CREATE ROLE createusermapping_00982_actor LOGIN NOSUPERUSER;
GRANT USAGE ON FOREIGN SERVER createusermapping_00982_noserver TO createusermapping_00982_actor;
SET ROLE createusermapping_00982_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE USER MAPPING。
-- primary-target-begin
CREATE USER MAPPING FOR CURRENT_USER SERVER createusermapping_00982_noserver;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FOREIGN DATA WRAPPER IF EXISTS createusermapping_00982_fdw CASCADE;
DROP SCHEMA IF EXISTS createusermapping_00982_schema CASCADE;
DROP OWNED BY createusermapping_00982_actor CASCADE;
DROP ROLE IF EXISTS createusermapping_00982_actor;
