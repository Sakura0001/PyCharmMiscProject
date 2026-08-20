-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP LANGUAGE target_object_state=exists_with_dependents
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPLANGUAGE00029
-- source_md: skills/pg-sql-generation/references/statements/ddl/language/drop_language.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/language/drop_language.yaml
-- primary_obligation_id: DROPLANGUAGE-SFV|sfv-6377dbf7c501fc0747e12200|drop_language
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS droplanguage_00029_depfn;
DROP LANGUAGE IF EXISTS droplanguage_00029_lang CASCADE;
DROP FUNCTION IF EXISTS droplanguage_00029_handler;
\set ON_ERROR_STOP on
-- 2. 创建完整本地语言和因子专用夹具。
CREATE FUNCTION droplanguage_00029_handler() RETURNS void AS $$ BEGIN END; $$ LANGUAGE plpgsql;
CREATE LANGUAGE droplanguage_00029_lang HANDLER droplanguage_00029_handler;
CREATE FUNCTION droplanguage_00029_depfn() RETURNS integer AS $$ BEGIN RETURN 1; END; $$ LANGUAGE droplanguage_00029_lang;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP LANGUAGE。
-- primary-target-begin
DROP LANGUAGE droplanguage_00029_lang;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS language_present FROM pg_catalog.pg_language WHERE lanname = 'droplanguage_00029_lang' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP FUNCTION IF EXISTS droplanguage_00029_depfn;
DROP LANGUAGE IF EXISTS droplanguage_00029_lang CASCADE;
DROP FUNCTION IF EXISTS droplanguage_00029_handler;
