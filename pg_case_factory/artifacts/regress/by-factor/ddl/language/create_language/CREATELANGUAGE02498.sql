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
-- case_id: CREATELANGUAGE02498
-- source_md: skills/pg-sql-generation/references/statements/ddl/language/create_language.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/language/create_language.yaml
-- primary_obligation_id: CLANG-EXT|02498|error_assertion|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS residual_check_no_objects;
DROP LANGUAGE IF EXISTS "createlanguage_02498_QLang" CASCADE;
DROP FUNCTION IF EXISTS createlanguage_02498_handler;
RESET ROLE;
DROP ROLE IF EXISTS createlanguage_02498_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createlanguage_02498_actor LOGIN NOSUPERUSER;
CREATE FUNCTION createlanguage_02498_handler() RETURNS language_handler AS 'plpgsql_call_handler' LANGUAGE C;
CREATE LANGUAGE "createlanguage_02498_QLang" HANDLER createlanguage_02498_handler;
SET ROLE createlanguage_02498_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE LANGUAGE。
-- primary-target-begin
CREATE OR REPLACE TRUSTED LANGUAGE "createlanguage_02498_QLang" HANDLER createlanguage_02498_handler;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP LANGUAGE IF EXISTS "createlanguage_02498_QLang" CASCADE;
DROP FUNCTION IF EXISTS createlanguage_02498_handler;
DROP OWNED BY createlanguage_02498_actor CASCADE;
DROP ROLE IF EXISTS createlanguage_02498_actor;
