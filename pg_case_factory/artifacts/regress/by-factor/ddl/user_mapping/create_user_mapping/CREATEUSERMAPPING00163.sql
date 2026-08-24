-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE USER MAPPING object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEUSERMAPPING00163
-- source_md: skills/pg-sql-generation/references/statements/ddl/user_mapping/create_user_mapping.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user_mapping/create_user_mapping.yaml
-- primary_obligation_id: CUM-EXT|00163|catalog_query_pg_user_mapping|drop_fdw|core_definition
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP USER MAPPING IF EXISTS FOR createusermapping_00163_user SERVER createusermapping_00163_server;
DROP SERVER IF EXISTS createusermapping_00163_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createusermapping_00163_fdw CASCADE;
DROP SCHEMA IF EXISTS createusermapping_00163_schema CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createusermapping_00163_user;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createusermapping_00163_schema;
CREATE FOREIGN DATA WRAPPER createusermapping_00163_fdw;
CREATE SERVER createusermapping_00163_server FOREIGN DATA WRAPPER createusermapping_00163_fdw;
CREATE ROLE createusermapping_00163_user LOGIN;
CREATE ROLE createusermapping_00163_user LOGIN;
CREATE USER MAPPING FOR createusermapping_00163_user SERVER createusermapping_00163_server OPTIONS (user 'val1');
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE USER MAPPING。
-- primary-target-begin
CREATE USER MAPPING FOR createusermapping_00163_user SERVER createusermapping_00163_server OPTIONS (user 'val1');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS mapping_state FROM pg_catalog.pg_user_mapping um JOIN pg_catalog.pg_foreign_server fs ON um.umserver = fs.oid WHERE fs.srvname = 'createusermapping_00163_server' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP USER MAPPING IF EXISTS FOR createusermapping_00163_user SERVER createusermapping_00163_server;
DROP SERVER IF EXISTS createusermapping_00163_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createusermapping_00163_fdw CASCADE;
DROP SCHEMA IF EXISTS createusermapping_00163_schema CASCADE;
DROP OWNED BY createusermapping_00163_user CASCADE;
DROP ROLE IF EXISTS createusermapping_00163_user;
