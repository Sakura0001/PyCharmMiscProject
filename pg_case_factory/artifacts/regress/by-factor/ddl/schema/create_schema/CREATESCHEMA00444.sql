-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE SCHEMA schema_name_shape=pg_prefix_reserved
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATESCHEMA00444
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/create_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/create_schema.yaml
-- primary_obligation_id: CSCHEMA-EXT|00444|information_schema_schemata|DROP_SCHEMA
-- expected_outcome: expected_failure
-- expected_sqlstate: 42939
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS pg_createschema_00444_bad CASCADE;
DROP OWNED BY createschema_00444_owner CASCADE;
DROP ROLE IF EXISTS createschema_00444_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createschema_00444_owner LOGIN;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE SCHEMA。
-- primary-target-begin
CREATE SCHEMA pg_createschema_00444_bad AUTHORIZATION CURRENT_ROLE CREATE TABLE createschema_00444_t (id integer);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42939' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS schema_state FROM information_schema.schemata WHERE schema_name = 'pg_createschema_00444_bad' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP SCHEMA pg_createschema_00444_bad CASCADE;
DROP OWNED BY createschema_00444_owner CASCADE;
DROP ROLE IF EXISTS createschema_00444_owner;
