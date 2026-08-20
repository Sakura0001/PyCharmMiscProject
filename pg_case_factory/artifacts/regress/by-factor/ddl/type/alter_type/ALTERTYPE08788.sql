-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TYPE target_action=alter_attribute_type
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTYPE08788
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/alter_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/alter_type.yaml
-- primary_obligation_id: ATYPE-EXT|08788|pg_attribute_query|DROP_TYPE_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertype_08788_t;
DROP TYPE IF EXISTS altertype_08788_type CASCADE;
DROP OWNED BY altertype_08788_owner CASCADE;
DROP ROLE IF EXISTS altertype_08788_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE altertype_08788_owner LOGIN;
SET ROLE altertype_08788_owner;
CREATE TYPE altertype_08788_type AS (altertype_08788_attr integer);
CREATE TABLE altertype_08788_t OF altertype_08788_type;
-- 3. 执行唯一获得覆盖信用的 ALTER TYPE。
-- primary-target-begin
ALTER TYPE altertype_08788_type ALTER ATTRIBUTE altertype_08788_attr TYPE timestamp;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS type_attributes FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_type t ON t.typrelid = a.attrelid WHERE t.typname = 'altertype_08788_type' AND a.attnum > 0 ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TYPE IF EXISTS altertype_08788_type CASCADE;
DROP OWNED BY altertype_08788_owner CASCADE;
DROP ROLE IF EXISTS altertype_08788_owner;
DROP TABLE IF EXISTS altertype_08788_t;
