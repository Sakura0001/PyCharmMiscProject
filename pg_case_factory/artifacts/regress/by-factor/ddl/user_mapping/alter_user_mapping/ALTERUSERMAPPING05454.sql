-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER USER MAPPING target_action=options
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERUSERMAPPING05454
-- source_md: skills/pg-sql-generation/references/statements/ddl/user_mapping/alter_user_mapping.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user_mapping/alter_user_mapping.yaml
-- primary_obligation_id: AUM-EXT|05454|error_assertion|drop_user_mapping
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP USER MAPPING IF EXISTS FOR alterusermapping_05454_actor SERVER alterusermapping_05454_server;
DROP USER MAPPING IF EXISTS FOR alterusermapping_05454_actor SERVER alterusermapping_05454_server;
DROP SERVER IF EXISTS alterusermapping_05454_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterusermapping_05454_fdw;
DROP OWNED BY alterusermapping_05454_actor CASCADE;
DROP ROLE IF EXISTS alterusermapping_05454_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FOREIGN DATA WRAPPER alterusermapping_05454_fdw;
CREATE SERVER alterusermapping_05454_server FOREIGN DATA WRAPPER alterusermapping_05454_fdw;
CREATE ROLE alterusermapping_05454_actor LOGIN NOSUPERUSER;
GRANT USAGE ON FOREIGN SERVER alterusermapping_05454_server TO alterusermapping_05454_actor;
CREATE USER MAPPING FOR alterusermapping_05454_actor SERVER alterusermapping_05454_server OPTIONS (ADD alterusermapping_05454_opt 'initial');
SET ROLE alterusermapping_05454_actor;
-- 3. 执行唯一获得覆盖信用的 ALTER USER MAPPING。
-- primary-target-begin
ALTER USER MAPPING FOR USER SERVER alterusermapping_05454_server OPTIONS (ADD alterusermapping_05454_opt 'val');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP USER MAPPING IF EXISTS FOR alterusermapping_05454_actor SERVER alterusermapping_05454_server;
DROP SERVER IF EXISTS alterusermapping_05454_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterusermapping_05454_fdw;
DROP OWNED BY alterusermapping_05454_actor CASCADE;
DROP ROLE IF EXISTS alterusermapping_05454_actor;
