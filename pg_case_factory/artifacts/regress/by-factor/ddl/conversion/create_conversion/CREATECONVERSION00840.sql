-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE CONVERSION privilege_level=non_owner_no_create
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATECONVERSION00840
-- source_md: skills/pg-sql-generation/references/statements/ddl/conversion/create_conversion.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/conversion/create_conversion.yaml
-- primary_obligation_id: CCONV-EXT|00840|catalog_query_pg_conversion|cascade_drop
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS createconversion_00840_func CASCADE;
DROP SCHEMA IF EXISTS createconversion_00840_schema CASCADE;
DROP OWNED BY createconversion_00840_nopriv CASCADE;
DROP ROLE IF EXISTS createconversion_00840_nopriv;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createconversion_00840_schema;
CREATE FUNCTION createconversion_00840_func (integer, integer, cstring, internal, integer, boolean) RETURNS integer LANGUAGE internal AS 'ascii_to_mic';
CREATE ROLE createconversion_00840_nopriv LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA createconversion_00840_schema TO createconversion_00840_nopriv;
SET ROLE createconversion_00840_nopriv;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE CONVERSION。
-- primary-target-begin
CREATE CONVERSION createconversion_00840_conv FOR 'UTF8' TO 'LATIN1' FROM createconversion_00840_func;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS conversion_state FROM pg_catalog.pg_conversion WHERE conname = 'createconversion_00840_conv' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION IF EXISTS createconversion_00840_func CASCADE;
DROP SCHEMA IF EXISTS createconversion_00840_schema CASCADE;
DROP OWNED BY createconversion_00840_nopriv CASCADE;
DROP ROLE IF EXISTS createconversion_00840_nopriv;
