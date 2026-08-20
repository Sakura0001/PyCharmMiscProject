-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER USER MAPPING privilege_level=non_privileged
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERUSERMAPPING03933
-- source_md: skills/pg-sql-generation/references/statements/ddl/user_mapping/alter_user_mapping.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user_mapping/alter_user_mapping.yaml
-- primary_obligation_id: AUM-EXT|03933|error_assertion|drop_user_mapping
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP USER MAPPING IF EXISTS FOR alterusermapping_03933_actor SERVER alterusermapping_03933_server;
DROP USER MAPPING IF EXISTS FOR alterusermapping_03933_actor SERVER alterusermapping_03933_server;
DROP SERVER IF EXISTS alterusermapping_03933_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterusermapping_03933_fdw;
DROP OWNED BY alterusermapping_03933_actor CASCADE;
DROP ROLE IF EXISTS alterusermapping_03933_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FOREIGN DATA WRAPPER alterusermapping_03933_fdw;
CREATE SERVER alterusermapping_03933_server FOREIGN DATA WRAPPER alterusermapping_03933_fdw;
CREATE ROLE alterusermapping_03933_actor LOGIN NOSUPERUSER;
CREATE USER MAPPING FOR alterusermapping_03933_actor SERVER alterusermapping_03933_server OPTIONS (ADD alterusermapping_03933_opt 'initial');
SET ROLE alterusermapping_03933_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER USER MAPPING。
-- primary-target-begin
ALTER USER MAPPING FOR SESSION_USER SERVER alterusermapping_03933_server OPTIONS (SET alterusermapping_03933_opt 'val');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP USER MAPPING IF EXISTS FOR alterusermapping_03933_actor SERVER alterusermapping_03933_server;
DROP SERVER IF EXISTS alterusermapping_03933_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterusermapping_03933_fdw;
DROP OWNED BY alterusermapping_03933_actor CASCADE;
DROP ROLE IF EXISTS alterusermapping_03933_actor;
