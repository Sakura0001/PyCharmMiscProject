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
-- case_id: ALTERTYPE09020
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/alter_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/alter_type.yaml
-- primary_obligation_id: ATYPE-EXT|09020|enum_value_query|DROP_TYPE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TYPE IF EXISTS altertype_09020_type CASCADE;
DROP OWNED BY altertype_09020_owner CASCADE;
DROP ROLE IF EXISTS altertype_09020_owner;
DROP OWNED BY altertype_09020_actor CASCADE;
DROP ROLE IF EXISTS altertype_09020_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE altertype_09020_owner LOGIN;
CREATE ROLE altertype_09020_actor LOGIN NOSUPERUSER;
SET ROLE altertype_09020_owner;
CREATE TYPE altertype_09020_type AS (altertype_09020_attr integer);
SET ROLE altertype_09020_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TYPE。
-- primary-target-begin
ALTER TYPE altertype_09020_type ALTER ATTRIBUTE altertype_09020_attr TYPE boolean RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS enum_values FROM pg_catalog.pg_enum e JOIN pg_catalog.pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'altertype_09020_type' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TYPE IF EXISTS altertype_09020_type CASCADE;
DROP OWNED BY altertype_09020_owner CASCADE;
DROP ROLE IF EXISTS altertype_09020_owner;
DROP OWNED BY altertype_09020_actor CASCADE;
DROP ROLE IF EXISTS altertype_09020_actor;
