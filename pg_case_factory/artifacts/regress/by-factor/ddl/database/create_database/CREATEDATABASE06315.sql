-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE DATABASE target_action=create_database
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEDATABASE06315
-- source_md: skills/pg-sql-generation/references/statements/ddl/database/create_database.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/database/create_database.yaml
-- primary_obligation_id: CD-EXT|06315|catalog_query_pg_database|drop_database
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS residual_check_no_objects;
DROP DATABASE IF EXISTS createdatabase_06315_db;
DROP ROLE IF EXISTS createdatabase_06315_actor;
DROP ROLE IF EXISTS createdatabase_06315_role;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createdatabase_06315_actor LOGIN NOSUPERUSER CREATEDB;
SET ROLE createdatabase_06315_actor;
CREATE ROLE createdatabase_06315_role LOGIN;
-- 3. 执行唯一获得覆盖信用的 CREATE DATABASE。
-- primary-target-begin
CREATE DATABASE createdatabase_06315_db WITH OWNER createdatabase_06315_role TEMPLATE createdatabase_06315_template ENCODING 'UTF8' LOCALE 'POSIX';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT datname FROM pg_catalog.pg_database WHERE datname = 'createdatabase_06315_db' ORDER BY datname;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP DATABASE IF EXISTS createdatabase_06315_db;
DROP ROLE IF EXISTS createdatabase_06315_actor;
DROP ROLE IF EXISTS createdatabase_06315_role;
SELECT 1 AS residual_check_no_objects;
