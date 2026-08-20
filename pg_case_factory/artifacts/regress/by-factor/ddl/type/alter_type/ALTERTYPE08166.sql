-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TYPE target_action=owner_to
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTYPE08166
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/alter_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/alter_type.yaml
-- primary_obligation_id: ATYPE-EXT|08166|information_schema_user_defined_types|DROP_TYPE_IF_EXISTS
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TYPE IF EXISTS altertype_08166_sch.altertype_08166_type CASCADE;
DROP OWNED BY altertype_08166_owner CASCADE;
DROP ROLE IF EXISTS altertype_08166_owner;
DROP SCHEMA IF EXISTS altertype_08166_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertype_08166_sch;
CREATE ROLE altertype_08166_owner LOGIN;
SET ROLE altertype_08166_owner;
GRANT CREATE ON SCHEMA altertype_08166_sch TO altertype_08166_newowner;
CREATE TYPE altertype_08166_sch.altertype_08166_type AS (altertype_08166_attr integer);
-- 3. 执行唯一获得覆盖信用的 ALTER TYPE。
-- primary-target-begin
ALTER TYPE altertype_08166_sch.altertype_08166_type OWNER TO SESSION_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS type_present FROM information_schema.user_defined_types WHERE user_defined_type_name = 'altertype_08166_type' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TYPE IF EXISTS altertype_08166_sch.altertype_08166_type CASCADE;
DROP OWNED BY altertype_08166_owner CASCADE;
DROP ROLE IF EXISTS altertype_08166_owner;
DROP SCHEMA IF EXISTS altertype_08166_sch CASCADE;
