-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SCHEMA rename_clause=new_existing_name
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSCHEMA02321
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/alter_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/alter_schema.yaml
-- primary_obligation_id: AS-EXT|02321|information_schema_schemata|DROP_SCHEMA_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterschema_02321_sch.alterschema_02321_tab CASCADE;
DROP SCHEMA IF EXISTS alterschema_02321_sch CASCADE;
DROP SCHEMA IF EXISTS alterschema_02321_existsch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA alterschema_02321_sch;
CREATE TABLE alterschema_02321_sch.alterschema_02321_tab (alterschema_02321_col integer);
CREATE SCHEMA alterschema_02321_existsch;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SCHEMA。
-- primary-target-begin
ALTER SCHEMA alterschema_02321_sch RENAME TO alterschema_02321_existsch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS schema_state FROM information_schema.schemata WHERE schema_name = 'alterschema_02321_sch' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS alterschema_02321_sch CASCADE;
DROP SCHEMA IF EXISTS alterschema_02321_existsch CASCADE;
DROP TABLE IF EXISTS alterschema_02321_sch.alterschema_02321_tab CASCADE;
