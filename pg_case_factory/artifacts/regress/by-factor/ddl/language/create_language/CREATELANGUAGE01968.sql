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
-- case_id: CREATELANGUAGE01968
-- source_md: skills/pg-sql-generation/references/statements/ddl/language/create_language.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/language/create_language.yaml
-- primary_obligation_id: CLANG-EXT|01968|effect_query|reset_state
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS residual_check_no_objects;
DROP LANGUAGE IF EXISTS createlanguage_01968_lang CASCADE;
DROP FUNCTION IF EXISTS createlanguage_01968_handler;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createlanguage_01968_handler() RETURNS language_handler AS 'plpgsql_call_handler' LANGUAGE C;
CREATE LANGUAGE createlanguage_01968_lang HANDLER createlanguage_01968_handler;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE LANGUAGE。
-- primary-target-begin
CREATE OR REPLACE LANGUAGE createlanguage_01968_lang HANDLER createlanguage_01968_handler;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT lanname FROM pg_catalog.pg_language WHERE lanname = 'createlanguage_01968_lang' ORDER BY lanname;
-- 5. 清理全部本编号对象。
DROP LANGUAGE IF EXISTS createlanguage_01968_lang CASCADE;
DROP FUNCTION IF EXISTS createlanguage_01968_handler;
