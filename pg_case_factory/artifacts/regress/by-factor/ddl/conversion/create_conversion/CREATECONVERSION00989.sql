-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE CONVERSION target_action=create_default_conversion
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATECONVERSION00989
-- source_md: skills/pg-sql-generation/references/statements/ddl/conversion/create_conversion.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/conversion/create_conversion.yaml
-- primary_obligation_id: CCONV-EXT|00989|error_assertion|drop_conversion
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CONVERSION IF EXISTS createconversion_00989_conv CASCADE;
DROP FUNCTION IF EXISTS createconversion_00989_schema.createconversion_00989_func CASCADE;
DROP SCHEMA IF EXISTS createconversion_00989_schema CASCADE;
DROP OWNED BY createconversion_00989_owner CASCADE;
DROP ROLE IF EXISTS createconversion_00989_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createconversion_00989_schema;
CREATE FUNCTION createconversion_00989_schema.createconversion_00989_func (integer, integer, cstring, internal, integer, boolean) RETURNS integer LANGUAGE internal AS 'ascii_to_mic';
CREATE ROLE createconversion_00989_owner LOGIN NOSUPERUSER;
GRANT CREATE ON SCHEMA createconversion_00989_schema TO createconversion_00989_owner;
GRANT USAGE ON SCHEMA createconversion_00989_schema TO createconversion_00989_owner;
SET ROLE createconversion_00989_owner;
-- 3. 执行唯一获得覆盖信用的 CREATE CONVERSION。
-- primary-target-begin
CREATE DEFAULT CONVERSION createconversion_00989_conv FOR 'UTF8' TO 'LATIN1' FROM createconversion_00989_schema.createconversion_00989_func;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP CONVERSION IF EXISTS createconversion_00989_conv CASCADE;
DROP FUNCTION IF EXISTS createconversion_00989_schema.createconversion_00989_func CASCADE;
DROP SCHEMA IF EXISTS createconversion_00989_schema CASCADE;
DROP OWNED BY createconversion_00989_owner CASCADE;
DROP ROLE IF EXISTS createconversion_00989_owner;
