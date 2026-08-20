-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP DATABASE privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPDATABASE00229
-- source_md: skills/pg-sql-generation/references/statements/ddl/database/drop_database.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/database/drop_database.yaml
-- primary_obligation_id: DROPDATABASE-EXT|00229|drop_database|notice_assertion_if_exists|drop_database_simple
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP DATABASE IF EXISTS "dropdatabase_00229_db";
DROP ROLE IF EXISTS dropdatabase_00229_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地数据库和因子专用夹具。
CREATE ROLE dropdatabase_00229_actor LOGIN NOSUPERUSER;
CREATE DATABASE "dropdatabase_00229_db";
SET ROLE dropdatabase_00229_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP DATABASE。
-- primary-target-begin
DROP DATABASE IF EXISTS "dropdatabase_00229_db" WITH (FORCE);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS database_present FROM pg_catalog.pg_database WHERE datname = 'dropdatabase_00229_db' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS dropdatabase_00229_actor;
DROP DATABASE IF EXISTS "dropdatabase_00229_db";
