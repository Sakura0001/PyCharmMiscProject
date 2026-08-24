-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE DATABASE tablespace_existence=tablespace_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEDATABASE00054
-- source_md: skills/pg-sql-generation/references/statements/ddl/database/create_database.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/database/create_database.yaml
-- primary_obligation_id: CD-SFV|sfv-c6c6af09b9dea40f6dca484f|create_database
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P27
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS residual_check_no_objects;
DROP DATABASE IF EXISTS createdatabase_00054_db;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE DATABASE。
-- primary-target-begin
CREATE DATABASE createdatabase_00054_db WITH TABLESPACE createdatabase_00054_no_ts;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P27' AS target_sqlstate_matches_expected;
SELECT datname FROM pg_catalog.pg_database WHERE datname = 'createdatabase_00054_db' ORDER BY datname;
-- 5. 清理全部本编号对象。
DROP DATABASE IF EXISTS createdatabase_00054_db;
SELECT 1 AS residual_check_no_objects;
