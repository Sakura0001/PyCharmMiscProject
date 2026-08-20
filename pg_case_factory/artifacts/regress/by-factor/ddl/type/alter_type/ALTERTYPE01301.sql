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
-- case_id: ALTERTYPE01301
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/alter_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/alter_type.yaml
-- primary_obligation_id: ATYPE-EXT|01301|information_schema_user_defined_types|DROP_TYPE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertype_01301_t;
DROP TYPE IF EXISTS altertype_01301_type CASCADE;
DROP OWNED BY altertype_01301_owner CASCADE;
DROP ROLE IF EXISTS altertype_01301_owner;
DROP OWNED BY altertype_01301_actor CASCADE;
DROP ROLE IF EXISTS altertype_01301_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE altertype_01301_owner LOGIN;
CREATE ROLE altertype_01301_actor LOGIN NOSUPERUSER;
SET ROLE altertype_01301_owner;
CREATE TYPE altertype_01301_type AS (altertype_01301_attr integer);
CREATE TABLE altertype_01301_t OF altertype_01301_type;
SET ROLE altertype_01301_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TYPE。
-- primary-target-begin
ALTER TYPE altertype_01301_type ADD ATTRIBUTE altertype_01301_attr text CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS type_present FROM information_schema.user_defined_types WHERE user_defined_type_name = 'altertype_01301_type' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TYPE IF EXISTS altertype_01301_type CASCADE;
DROP OWNED BY altertype_01301_owner CASCADE;
DROP ROLE IF EXISTS altertype_01301_owner;
DROP OWNED BY altertype_01301_actor CASCADE;
DROP ROLE IF EXISTS altertype_01301_actor;
DROP TABLE IF EXISTS altertype_01301_t;
