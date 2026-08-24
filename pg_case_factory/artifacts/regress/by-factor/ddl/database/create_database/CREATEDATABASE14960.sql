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
-- case_id: CREATEDATABASE14960
-- source_md: skills/pg-sql-generation/references/statements/ddl/database/create_database.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/database/create_database.yaml
-- primary_obligation_id: CD-EXT|14960|error_assertion|force_drop_database
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P04
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS residual_check_no_objects;
DROP DATABASE IF EXISTS createdatabase_14960_db;
DROP ROLE IF EXISTS createdatabase_14960_role;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE DATABASE createdatabase_14960_db;
CREATE ROLE createdatabase_14960_role LOGIN;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE DATABASE。
-- primary-target-begin
CREATE DATABASE createdatabase_14960_db WITH OWNER createdatabase_14960_role TEMPLATE createdatabase_14960_template LOCALE 'C';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P04' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP DATABASE IF EXISTS createdatabase_14960_db WITH (FORCE);
DROP ROLE IF EXISTS createdatabase_14960_role;
SELECT 1 AS residual_check_no_objects;
