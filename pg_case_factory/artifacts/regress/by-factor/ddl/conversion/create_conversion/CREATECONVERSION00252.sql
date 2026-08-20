-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE CONVERSION conversion_function_state=function_exists_invalid_signature
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATECONVERSION00252
-- source_md: skills/pg-sql-generation/references/statements/ddl/conversion/create_conversion.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/conversion/create_conversion.yaml
-- primary_obligation_id: CCONV-EXT|00252|catalog_query_pg_conversion|cascade_drop
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P13
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS createconversion_00252_func CASCADE;
DROP SCHEMA IF EXISTS createconversion_00252_schema CASCADE;
DROP OWNED BY createconversion_00252_owner CASCADE;
DROP ROLE IF EXISTS createconversion_00252_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createconversion_00252_schema;
CREATE FUNCTION createconversion_00252_func(text) RETURNS text LANGUAGE plpgsql AS $$BEGIN RETURN 'x'; END$$;
CREATE ROLE createconversion_00252_owner LOGIN NOSUPERUSER;
GRANT CREATE ON SCHEMA createconversion_00252_schema TO createconversion_00252_owner;
GRANT USAGE ON SCHEMA createconversion_00252_schema TO createconversion_00252_owner;
SET ROLE createconversion_00252_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE CONVERSION。
-- primary-target-begin
CREATE DEFAULT CONVERSION createconversion_00252_conv FOR 'UTF8' TO 'LATIN1' FROM createconversion_00252_func;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42P13' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS conversion_state FROM pg_catalog.pg_conversion WHERE conname = 'createconversion_00252_conv' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION IF EXISTS createconversion_00252_func CASCADE;
DROP SCHEMA IF EXISTS createconversion_00252_schema CASCADE;
DROP OWNED BY createconversion_00252_owner CASCADE;
DROP ROLE IF EXISTS createconversion_00252_owner;
