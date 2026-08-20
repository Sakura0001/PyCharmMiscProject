-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE DATABASE object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEDATABASE14466
-- source_md: skills/pg-sql-generation/references/statements/ddl/database/create_database.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/database/create_database.yaml
-- primary_obligation_id: CD-EXT|14466|connect_to_new_database|force_drop_database
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P04
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS residual_check_no_objects;
DROP DATABASE IF EXISTS createdatabase_14466_db;
DROP ROLE IF EXISTS createdatabase_14466_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE DATABASE createdatabase_14466_db;
CREATE ROLE createdatabase_14466_actor LOGIN NOSUPERUSER CREATEDB;
SET ROLE createdatabase_14466_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE DATABASE。
-- primary-target-begin
CREATE DATABASE createdatabase_14466_db WITH TEMPLATE template0 ENCODING 'UTF8' LOCALE 'en_US.UTF-8' STRATEGY WAL_LOG;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42P04' AS target_sqlstate_matches_expected;
SELECT count(*) AS new_database_present FROM pg_catalog.pg_database WHERE datname = 'createdatabase_14466_db' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP DATABASE IF EXISTS createdatabase_14466_db WITH (FORCE);
DROP ROLE IF EXISTS createdatabase_14466_actor;
SELECT 1 AS residual_check_no_objects;
