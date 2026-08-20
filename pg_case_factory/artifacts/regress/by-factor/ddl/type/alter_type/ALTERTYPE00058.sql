-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TYPE owner_change_privilege=cannot_SET_ROLE
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTYPE00058
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/alter_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/alter_type.yaml
-- primary_obligation_id: ATYPE-SFV|sfv-66146a966ebe4f075013e69a|owner_to
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TYPE IF EXISTS altertype_00058_type CASCADE;
DROP OWNED BY altertype_00058_owner CASCADE;
DROP ROLE IF EXISTS altertype_00058_owner;
DROP OWNED BY altertype_00058_newowner CASCADE;
DROP ROLE IF EXISTS altertype_00058_newowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE altertype_00058_owner LOGIN;
CREATE ROLE altertype_00058_newowner LOGIN;
SET ROLE altertype_00058_owner;
GRANT CREATE ON SCHEMA altertype_00058_sch TO altertype_00058_newowner;
CREATE TYPE altertype_00058_type AS (altertype_00058_attr integer);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TYPE。
-- primary-target-begin
ALTER TYPE altertype_00058_type OWNER TO altertype_00058_newowner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS type_present FROM pg_catalog.pg_type WHERE typname = 'altertype_00058_type' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TYPE IF EXISTS altertype_00058_type CASCADE;
DROP OWNED BY altertype_00058_owner CASCADE;
DROP ROLE IF EXISTS altertype_00058_owner;
DROP OWNED BY altertype_00058_newowner CASCADE;
DROP ROLE IF EXISTS altertype_00058_newowner;
