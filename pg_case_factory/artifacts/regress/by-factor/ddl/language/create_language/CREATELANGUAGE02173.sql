-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE LANGUAGE privilege_context=non_superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATELANGUAGE02173
-- source_md: skills/pg-sql-generation/references/statements/ddl/language/create_language.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/language/create_language.yaml
-- primary_obligation_id: CLANG-EXT|02173|error_assertion|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS residual_check_no_objects;
DROP LANGUAGE IF EXISTS createlanguage_02173_lang CASCADE;
DROP FUNCTION IF EXISTS createlanguage_02173_handler;
DROP FUNCTION IF EXISTS createlanguage_02173_validator;
RESET ROLE;
DROP ROLE IF EXISTS createlanguage_02173_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createlanguage_02173_actor LOGIN NOSUPERUSER;
CREATE FUNCTION createlanguage_02173_handler() RETURNS language_handler AS 'plpgsql_call_handler' LANGUAGE C;
CREATE FUNCTION createlanguage_02173_validator(oid) RETURNS void AS 'plpgsql_validator' LANGUAGE C;
CREATE LANGUAGE createlanguage_02173_lang HANDLER createlanguage_02173_handler;
SET ROLE createlanguage_02173_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE LANGUAGE。
-- primary-target-begin
CREATE OR REPLACE LANGUAGE createlanguage_02173_lang HANDLER createlanguage_02173_handler VALIDATOR createlanguage_02173_validator;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP LANGUAGE IF EXISTS createlanguage_02173_lang CASCADE;
DROP FUNCTION IF EXISTS createlanguage_02173_handler;
DROP FUNCTION IF EXISTS createlanguage_02173_validator;
DROP OWNED BY createlanguage_02173_actor CASCADE;
DROP ROLE IF EXISTS createlanguage_02173_actor;
