-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE USER MAPPING options_clause=multiple_options
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEUSERMAPPING00022
-- source_md: skills/pg-sql-generation/references/statements/ddl/user_mapping/create_user_mapping.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user_mapping/create_user_mapping.yaml
-- primary_obligation_id: CUM-SFV|sfv-abdf281e8039b904f21e7d63|define_mapping
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP USER MAPPING IF EXISTS FOR createusermapping_00022_user SERVER createusermapping_00022_server;
DROP SERVER IF EXISTS createusermapping_00022_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createusermapping_00022_fdw CASCADE;
DROP SCHEMA IF EXISTS createusermapping_00022_schema CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createusermapping_00022_user;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createusermapping_00022_schema;
CREATE FOREIGN DATA WRAPPER createusermapping_00022_fdw;
CREATE SERVER createusermapping_00022_server FOREIGN DATA WRAPPER createusermapping_00022_fdw;
CREATE ROLE createusermapping_00022_user LOGIN;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE USER MAPPING。
-- primary-target-begin
CREATE USER MAPPING FOR createusermapping_00022_user SERVER createusermapping_00022_server OPTIONS (user 'val1', password 'val2');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS mapping_state FROM pg_catalog.pg_user_mapping um JOIN pg_catalog.pg_foreign_server fs ON um.umserver = fs.oid WHERE fs.srvname = 'createusermapping_00022_server' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP USER MAPPING IF EXISTS FOR createusermapping_00022_user SERVER createusermapping_00022_server;
DROP SCHEMA IF EXISTS createusermapping_00022_schema CASCADE;
DROP OWNED BY createusermapping_00022_user CASCADE;
DROP ROLE IF EXISTS createusermapping_00022_user;
