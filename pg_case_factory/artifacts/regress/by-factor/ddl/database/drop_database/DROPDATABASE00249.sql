-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP DATABASE object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPDATABASE00249
-- source_md: skills/pg-sql-generation/references/statements/ddl/database/drop_database.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/database/drop_database.yaml
-- primary_obligation_id: DROPDATABASE-EXT|00249|drop_database|catalog_query_pg_database_absence|drop_database_simple
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP DATABASE IF EXISTS "dropdatabase_00249_db";
\set ON_ERROR_STOP on
-- 2. 创建完整本地数据库和因子专用夹具。
CREATE DATABASE "dropdatabase_00249_db";
-- 3. 执行唯一获得覆盖信用的 DROP DATABASE。
-- primary-target-begin
DROP DATABASE IF EXISTS "dropdatabase_00249_db";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS database_absent FROM pg_catalog.pg_database WHERE datname = 'dropdatabase_00249_db' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP DATABASE IF EXISTS "dropdatabase_00249_db";
