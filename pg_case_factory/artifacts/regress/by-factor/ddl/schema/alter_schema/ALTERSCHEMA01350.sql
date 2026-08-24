-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SCHEMA target_action=owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSCHEMA01350
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/alter_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/alter_schema.yaml
-- primary_obligation_id: AS-EXT|01350|information_schema_schemata|DROP_SCHEMA_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS alterschema_01350_sch CASCADE;
DROP OWNED BY alterschema_01350_newowner CASCADE;
DROP ROLE IF EXISTS alterschema_01350_newowner;
DROP OWNED BY alterschema_01350_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_01350_schowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterschema_01350_schowner LOGIN;
CREATE ROLE alterschema_01350_newowner LOGIN;
GRANT CREATE ON DATABASE pgcf TO alterschema_01350_newowner;
CREATE SCHEMA alterschema_01350_sch;
ALTER SCHEMA alterschema_01350_sch OWNER TO alterschema_01350_schowner;
GRANT alterschema_01350_newowner TO alterschema_01350_schowner;
SET ROLE alterschema_01350_schowner;
-- 3. 执行唯一获得覆盖信用的 ALTER SCHEMA。
-- primary-target-begin
ALTER SCHEMA alterschema_01350_sch OWNER TO alterschema_01350_newowner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS schema_state FROM information_schema.schemata WHERE schema_name = 'alterschema_01350_sch' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS alterschema_01350_sch CASCADE;
DROP OWNED BY alterschema_01350_newowner CASCADE;
DROP ROLE IF EXISTS alterschema_01350_newowner;
DROP OWNED BY alterschema_01350_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_01350_schowner;
