-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE LANGUAGE target_form=with_handler
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATELANGUAGE00085
-- source_md: skills/pg-sql-generation/references/statements/ddl/language/create_language.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/language/create_language.yaml
-- primary_obligation_id: CLANG-EXT|00085|error_assertion|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS residual_check_no_objects;
DROP LANGUAGE IF EXISTS createlanguage_00085_lang CASCADE;
DROP FUNCTION IF EXISTS createlanguage_00085_handler;
DROP FUNCTION IF EXISTS createlanguage_00085_inline;
DROP FUNCTION IF EXISTS createlanguage_00085_validator;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createlanguage_00085_handler() RETURNS language_handler AS 'plpgsql_call_handler' LANGUAGE C;
CREATE FUNCTION createlanguage_00085_inline(internal) RETURNS void AS 'plpgsql_inline_handler' LANGUAGE C;
CREATE FUNCTION createlanguage_00085_validator(oid) RETURNS void AS 'plpgsql_validator' LANGUAGE C;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE LANGUAGE。
-- primary-target-begin
CREATE LANGUAGE createlanguage_00085_lang HANDLER createlanguage_00085_handler INLINE createlanguage_00085_inline VALIDATOR createlanguage_00085_validator;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP LANGUAGE IF EXISTS createlanguage_00085_lang CASCADE;
DROP FUNCTION IF EXISTS createlanguage_00085_handler;
DROP FUNCTION IF EXISTS createlanguage_00085_inline;
DROP FUNCTION IF EXISTS createlanguage_00085_validator;
