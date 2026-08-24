-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP LANGUAGE dependency_state=has_dependents
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPLANGUAGE00444
-- source_md: skills/pg-sql-generation/references/statements/ddl/language/drop_language.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/language/drop_language.yaml
-- primary_obligation_id: DROPLANGUAGE-EXT|00444|drop_language|catalog_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS droplanguage_00444_depfn;
DROP LANGUAGE IF EXISTS droplanguage_00444_lang CASCADE;
DROP FUNCTION IF EXISTS droplanguage_00444_handler;
\set ON_ERROR_STOP on
-- 2. 创建完整本地语言和因子专用夹具。
SELECT 1 AS target_language_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP LANGUAGE。
-- primary-target-begin
DROP LANGUAGE IF EXISTS droplanguage_00444_lang RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS language_absent FROM pg_catalog.pg_language WHERE lanname = 'droplanguage_00444_lang' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP FUNCTION IF EXISTS droplanguage_00444_depfn;
DROP LANGUAGE IF EXISTS droplanguage_00444_lang CASCADE;
DROP FUNCTION IF EXISTS droplanguage_00444_handler;
