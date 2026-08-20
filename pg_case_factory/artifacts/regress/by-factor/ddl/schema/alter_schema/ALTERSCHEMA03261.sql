-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SCHEMA object_state=not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSCHEMA03261
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/alter_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/alter_schema.yaml
-- primary_obligation_id: AS-EXT|03261|current_schema_query|DROP_SCHEMA_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 3F000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OWNED BY alterschema_03261_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_03261_schowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterschema_03261_schowner LOGIN;
SELECT 1 AS target_schema_intentionally_absent;
SET ROLE alterschema_03261_schowner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SCHEMA。
-- primary-target-begin
ALTER SCHEMA alterschema_03261_sch OWNER TO SESSION_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '3F000' AS target_sqlstate_matches_expected;
SELECT current_schema() IS DISTINCT FROM 'alterschema_03261_sch' AS schema_absent;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY alterschema_03261_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_03261_schowner;
