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
-- case_id: ALTERUSERMAPPING02623
-- source_md: skills/pg-sql-generation/references/statements/ddl/user_mapping/alter_user_mapping.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user_mapping/alter_user_mapping.yaml
-- primary_obligation_id: AUM-EXT|02623|catalog_query_pg_user_mapping|drop_server
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SERVER IF EXISTS alterusermapping_02623_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterusermapping_02623_fdw;
DROP OWNED BY alterusermapping_02623_actor CASCADE;
DROP ROLE IF EXISTS alterusermapping_02623_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FOREIGN DATA WRAPPER alterusermapping_02623_fdw;
CREATE SERVER alterusermapping_02623_server FOREIGN DATA WRAPPER alterusermapping_02623_fdw;
CREATE ROLE alterusermapping_02623_actor LOGIN NOSUPERUSER;
GRANT USAGE ON FOREIGN SERVER alterusermapping_02623_server TO alterusermapping_02623_actor;
SELECT 1 AS target_user_mapping_intentionally_absent;
SET ROLE alterusermapping_02623_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER USER MAPPING。
-- primary-target-begin
ALTER USER MAPPING FOR PUBLIC SERVER alterusermapping_02623_server OPTIONS (SET alterusermapping_02623_opt 'val');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS mapping_state FROM pg_catalog.pg_user_mapping WHERE umserver = (SELECT oid FROM pg_catalog.pg_foreign_server WHERE srvname = 'alterusermapping_02623_server') ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SERVER IF EXISTS alterusermapping_02623_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterusermapping_02623_fdw;
DROP OWNED BY alterusermapping_02623_actor CASCADE;
DROP ROLE IF EXISTS alterusermapping_02623_actor;
