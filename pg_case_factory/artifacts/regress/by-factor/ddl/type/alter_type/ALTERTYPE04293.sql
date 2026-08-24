-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TYPE privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTYPE04293
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/alter_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/alter_type.yaml
-- primary_obligation_id: ATYPE-EXT|04293|enum_value_query|DROP_TYPE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TYPE IF EXISTS altertype_04293_sch.altertype_04293_type CASCADE;
DROP OWNED BY altertype_04293_owner CASCADE;
DROP ROLE IF EXISTS altertype_04293_owner;
DROP OWNED BY altertype_04293_actor CASCADE;
DROP ROLE IF EXISTS altertype_04293_actor;
DROP SCHEMA IF EXISTS altertype_04293_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertype_04293_sch;
CREATE ROLE altertype_04293_owner LOGIN;
CREATE ROLE altertype_04293_actor LOGIN NOSUPERUSER;
SET ROLE altertype_04293_owner;
GRANT CREATE ON SCHEMA altertype_04293_sch TO altertype_04293_newowner;
CREATE TYPE altertype_04293_sch.altertype_04293_type AS (altertype_04293_attr integer);
SET ROLE altertype_04293_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TYPE。
-- primary-target-begin
ALTER TYPE altertype_04293_sch.altertype_04293_type OWNER TO SESSION_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS enum_values FROM pg_catalog.pg_enum e JOIN pg_catalog.pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'altertype_04293_type' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TYPE IF EXISTS altertype_04293_sch.altertype_04293_type CASCADE;
DROP OWNED BY altertype_04293_owner CASCADE;
DROP ROLE IF EXISTS altertype_04293_owner;
DROP OWNED BY altertype_04293_actor CASCADE;
DROP ROLE IF EXISTS altertype_04293_actor;
DROP SCHEMA IF EXISTS altertype_04293_sch CASCADE;
