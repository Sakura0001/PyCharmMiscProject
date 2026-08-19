-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER LANGUAGE privilege_context=owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERLANGUAGE00030
-- source_md: skills/pg-sql-generation/references/statements/ddl/language/alter_language.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/language/alter_language.yaml
-- primary_obligation_id: AL-SFV|sfv-75312a053b2c2026edc121f4|rename
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP LANGUAGE IF EXISTS alterlanguage_00030_lang CASCADE;
DROP LANGUAGE IF EXISTS alterlanguage_00030_renamed CASCADE;
DROP FUNCTION IF EXISTS alterlanguage_00030_handler() CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地语言和因子专用夹具。
CREATE FUNCTION alterlanguage_00030_handler() RETURNS language_handler AS '$libdir/plpgsql', 'plpgsql_call_handler' LANGUAGE C;
CREATE LANGUAGE alterlanguage_00030_lang HANDLER alterlanguage_00030_handler;
-- 3. 执行唯一获得覆盖信用的 ALTER LANGUAGE。
-- primary-target-begin
ALTER LANGUAGE alterlanguage_00030_lang RENAME TO alterlanguage_00030_renamed;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS language_present FROM pg_catalog.pg_language WHERE lanname = 'alterlanguage_00030_renamed' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP LANGUAGE IF EXISTS alterlanguage_00030_lang CASCADE;
DROP LANGUAGE IF EXISTS alterlanguage_00030_renamed CASCADE;
DROP FUNCTION IF EXISTS alterlanguage_00030_handler() CASCADE;
