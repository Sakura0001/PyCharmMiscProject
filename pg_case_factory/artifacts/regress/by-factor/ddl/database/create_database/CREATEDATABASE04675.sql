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
-- case_id: CREATEDATABASE04675
-- source_md: skills/pg-sql-generation/references/statements/ddl/database/create_database.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/database/create_database.yaml
-- primary_obligation_id: CD-EXT|04675|error_assertion|drop_database
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS residual_check_no_objects;
DROP DATABASE IF EXISTS createdatabase_04675_db;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
-- 3. 执行唯一获得覆盖信用的 CREATE DATABASE。
-- primary-target-begin
CREATE DATABASE createdatabase_04675_db WITH OWNER CURRENT_USER TEMPLATE template0 ENCODING 'SQL_ASCII' LOCALE 'en_US.UTF-8' STRATEGY FILE_COPY;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP DATABASE IF EXISTS createdatabase_04675_db;
SELECT 1 AS residual_check_no_objects;
