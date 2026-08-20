-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE CONVERSION object_state=same_encoding_pair_default_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATECONVERSION00540
-- source_md: skills/pg-sql-generation/references/statements/ddl/conversion/create_conversion.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/conversion/create_conversion.yaml
-- primary_obligation_id: CCONV-EXT|00540|catalog_query_pg_conversion|cascade_drop
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CONVERSION IF EXISTS createconversion_00540_existingdef CASCADE;
DROP FUNCTION IF EXISTS createconversion_00540_func CASCADE;
DROP SCHEMA IF EXISTS createconversion_00540_schema CASCADE;
DROP OWNED BY createconversion_00540_owner CASCADE;
DROP ROLE IF EXISTS createconversion_00540_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createconversion_00540_schema;
CREATE FUNCTION createconversion_00540_func (integer, integer, cstring, internal, integer, boolean) RETURNS integer LANGUAGE internal AS 'ascii_to_mic';
CREATE DEFAULT CONVERSION createconversion_00540_existingdef FOR 'UTF8' TO 'LATIN1' FROM createconversion_00540_func;
CREATE ROLE createconversion_00540_owner LOGIN NOSUPERUSER;
GRANT CREATE ON SCHEMA createconversion_00540_schema TO createconversion_00540_owner;
GRANT USAGE ON SCHEMA createconversion_00540_schema TO createconversion_00540_owner;
SET ROLE createconversion_00540_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE CONVERSION。
-- primary-target-begin
CREATE DEFAULT CONVERSION createconversion_00540_language FOR 'UTF8' TO 'LATIN1' FROM createconversion_00540_func;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS conversion_state FROM pg_catalog.pg_conversion WHERE conname = 'createconversion_00540_language' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP CONVERSION IF EXISTS createconversion_00540_existingdef CASCADE;
DROP FUNCTION IF EXISTS createconversion_00540_func CASCADE;
DROP SCHEMA IF EXISTS createconversion_00540_schema CASCADE;
DROP OWNED BY createconversion_00540_owner CASCADE;
DROP ROLE IF EXISTS createconversion_00540_owner;
