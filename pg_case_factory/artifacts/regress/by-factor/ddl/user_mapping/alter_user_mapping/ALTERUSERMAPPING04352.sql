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
-- case_id: ALTERUSERMAPPING04352
-- source_md: skills/pg-sql-generation/references/statements/ddl/user_mapping/alter_user_mapping.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user_mapping/alter_user_mapping.yaml
-- primary_obligation_id: AUM-EXT|04352|option_query|revert_option
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
ALTER USER MAPPING FOR alterusermapping_04352_actor SERVER alterusermapping_04352_server OPTIONS (DROP alterusermapping_04352_opt);
DROP USER MAPPING IF EXISTS FOR alterusermapping_04352_actor SERVER alterusermapping_04352_server;
DROP SERVER IF EXISTS alterusermapping_04352_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterusermapping_04352_fdw;
DROP OWNED BY alterusermapping_04352_actor CASCADE;
DROP ROLE IF EXISTS alterusermapping_04352_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FOREIGN DATA WRAPPER alterusermapping_04352_fdw;
CREATE SERVER alterusermapping_04352_server FOREIGN DATA WRAPPER alterusermapping_04352_fdw;
CREATE ROLE alterusermapping_04352_actor LOGIN NOSUPERUSER;
CREATE USER MAPPING FOR alterusermapping_04352_actor SERVER alterusermapping_04352_server OPTIONS (ADD alterusermapping_04352_opt 'initial');
SET ROLE alterusermapping_04352_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER USER MAPPING。
-- primary-target-begin
ALTER USER MAPPING FOR alterusermapping_04352_actor SERVER alterusermapping_04352_server OPTIONS (SET alterusermapping_04352_opt 'val');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS mapping_state FROM pg_catalog.pg_user_mapping WHERE umserver = (SELECT oid FROM pg_catalog.pg_foreign_server WHERE srvname = 'alterusermapping_04352_server') ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP USER MAPPING IF EXISTS FOR alterusermapping_04352_actor SERVER alterusermapping_04352_server;
DROP SERVER IF EXISTS alterusermapping_04352_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterusermapping_04352_fdw;
DROP OWNED BY alterusermapping_04352_actor CASCADE;
DROP ROLE IF EXISTS alterusermapping_04352_actor;
