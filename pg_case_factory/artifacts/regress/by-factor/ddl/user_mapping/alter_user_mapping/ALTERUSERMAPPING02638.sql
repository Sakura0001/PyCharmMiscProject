-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER USER MAPPING object_state=not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERUSERMAPPING02638
-- source_md: skills/pg-sql-generation/references/statements/ddl/user_mapping/alter_user_mapping.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user_mapping/alter_user_mapping.yaml
-- primary_obligation_id: AUM-EXT|02638|error_assertion|drop_server
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SERVER IF EXISTS alterusermapping_02638_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterusermapping_02638_fdw;
DROP OWNED BY alterusermapping_02638_actor CASCADE;
DROP ROLE IF EXISTS alterusermapping_02638_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FOREIGN DATA WRAPPER alterusermapping_02638_fdw;
CREATE SERVER alterusermapping_02638_server FOREIGN DATA WRAPPER alterusermapping_02638_fdw;
CREATE ROLE alterusermapping_02638_actor LOGIN NOSUPERUSER;
GRANT USAGE ON FOREIGN SERVER alterusermapping_02638_server TO alterusermapping_02638_actor;
SELECT 1 AS target_user_mapping_intentionally_absent;
SET ROLE alterusermapping_02638_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER USER MAPPING。
-- primary-target-begin
ALTER USER MAPPING FOR SESSION_USER SERVER alterusermapping_02638_server OPTIONS (SET alterusermapping_02638_opt 'val');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SERVER IF EXISTS alterusermapping_02638_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterusermapping_02638_fdw;
DROP OWNED BY alterusermapping_02638_actor CASCADE;
DROP ROLE IF EXISTS alterusermapping_02638_actor;
