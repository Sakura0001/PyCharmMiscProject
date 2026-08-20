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
-- case_id: CREATECONVERSION00193
-- source_md: skills/pg-sql-generation/references/statements/ddl/conversion/create_conversion.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/conversion/create_conversion.yaml
-- primary_obligation_id: CCONV-EXT|00193|error_assertion|drop_conversion
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P13
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS createconversion_00193_func CASCADE;
DROP SCHEMA IF EXISTS createconversion_00193_schema CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createconversion_00193_schema;
CREATE FUNCTION createconversion_00193_func(text) RETURNS text LANGUAGE plpgsql AS $$BEGIN RETURN 'x'; END$$;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE CONVERSION。
-- primary-target-begin
CREATE DEFAULT CONVERSION createconversion_00193_schema.createconversion_00193_conv FOR 'UTF8' TO 'LATIN1' FROM createconversion_00193_func;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P13' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP FUNCTION IF EXISTS createconversion_00193_func CASCADE;
DROP SCHEMA IF EXISTS createconversion_00193_schema CASCADE;
