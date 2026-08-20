-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SCHEMA owner_change_privilege=cannot_SET_ROLE_to_new_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSCHEMA02934
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/alter_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/alter_schema.yaml
-- primary_obligation_id: AS-EXT|02934|information_schema_schemata|DROP_SCHEMA_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS alterschema_02934_sch CASCADE;
DROP OWNED BY alterschema_02934_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_02934_schowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterschema_02934_schowner LOGIN;
CREATE SCHEMA alterschema_02934_sch;
ALTER SCHEMA alterschema_02934_sch OWNER TO alterschema_02934_schowner;
CREATE VIEW alterschema_02934_sch.alterschema_02934_v AS SELECT 1 AS alterschema_02934_vcol;
SET ROLE alterschema_02934_schowner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SCHEMA。
-- primary-target-begin
ALTER SCHEMA alterschema_02934_sch OWNER TO CURRENT_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS schema_state FROM information_schema.schemata WHERE schema_name = 'alterschema_02934_sch' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS alterschema_02934_sch CASCADE;
DROP OWNED BY alterschema_02934_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_02934_schowner;
