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
-- case_id: ALTERTYPE01358
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/alter_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/alter_type.yaml
-- primary_obligation_id: ATYPE-EXT|01358|pg_attribute_query|DROP_TYPE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertype_01358_t;
DROP TYPE IF EXISTS altertype_01358_type CASCADE;
DROP OWNED BY altertype_01358_owner CASCADE;
DROP ROLE IF EXISTS altertype_01358_owner;
DROP OWNED BY altertype_01358_actor CASCADE;
DROP ROLE IF EXISTS altertype_01358_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE altertype_01358_owner LOGIN;
CREATE ROLE altertype_01358_actor LOGIN NOSUPERUSER;
SET ROLE altertype_01358_owner;
CREATE TYPE altertype_01358_type AS (altertype_01358_attr integer);
CREATE TABLE altertype_01358_t OF altertype_01358_type;
SET ROLE altertype_01358_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TYPE。
-- primary-target-begin
ALTER TYPE altertype_01358_type ALTER ATTRIBUTE altertype_01358_attr TYPE character varying CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS type_attributes FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_type t ON t.typrelid = a.attrelid WHERE t.typname = 'altertype_01358_type' AND a.attnum > 0 ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TYPE IF EXISTS altertype_01358_type CASCADE;
DROP OWNED BY altertype_01358_owner CASCADE;
DROP ROLE IF EXISTS altertype_01358_owner;
DROP OWNED BY altertype_01358_actor CASCADE;
DROP ROLE IF EXISTS altertype_01358_actor;
DROP TABLE IF EXISTS altertype_01358_t;
