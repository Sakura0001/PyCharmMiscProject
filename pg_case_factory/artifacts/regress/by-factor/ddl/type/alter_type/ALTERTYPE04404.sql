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
-- case_id: ALTERTYPE04404
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/alter_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/alter_type.yaml
-- primary_obligation_id: ATYPE-EXT|04404|pg_type_catalog_query|DROP_TYPE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TYPE IF EXISTS altertype_04404_sch.altertype_04404_type CASCADE;
DROP OWNED BY altertype_04404_owner CASCADE;
DROP ROLE IF EXISTS altertype_04404_owner;
DROP OWNED BY altertype_04404_actor CASCADE;
DROP ROLE IF EXISTS altertype_04404_actor;
DROP OWNED BY altertype_04404_newowner CASCADE;
DROP ROLE IF EXISTS altertype_04404_newowner;
DROP SCHEMA IF EXISTS altertype_04404_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertype_04404_sch;
CREATE ROLE altertype_04404_owner LOGIN;
CREATE ROLE altertype_04404_actor LOGIN NOSUPERUSER;
CREATE ROLE altertype_04404_newowner LOGIN;
SET ROLE altertype_04404_owner;
GRANT altertype_04404_newowner TO altertype_04404_owner;
GRANT CREATE ON SCHEMA altertype_04404_sch TO altertype_04404_newowner;
CREATE TYPE altertype_04404_sch.altertype_04404_type AS (altertype_04404_attr integer);
SET ROLE altertype_04404_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TYPE。
-- primary-target-begin
ALTER TYPE altertype_04404_sch.altertype_04404_type OWNER TO altertype_04404_newowner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS type_present FROM pg_catalog.pg_type WHERE typname = 'altertype_04404_type' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TYPE IF EXISTS altertype_04404_sch.altertype_04404_type CASCADE;
DROP OWNED BY altertype_04404_owner CASCADE;
DROP ROLE IF EXISTS altertype_04404_owner;
DROP OWNED BY altertype_04404_actor CASCADE;
DROP ROLE IF EXISTS altertype_04404_actor;
DROP OWNED BY altertype_04404_newowner CASCADE;
DROP ROLE IF EXISTS altertype_04404_newowner;
DROP SCHEMA IF EXISTS altertype_04404_sch CASCADE;
