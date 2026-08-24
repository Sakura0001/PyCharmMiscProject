-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP LANGUAGE target_object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPLANGUAGE00182
-- source_md: skills/pg-sql-generation/references/statements/ddl/language/drop_language.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/language/drop_language.yaml
-- primary_obligation_id: DROPLANGUAGE-EXT|00182|drop_language|effect_query|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP LANGUAGE IF EXISTS droplanguage_00182_lang CASCADE;
DROP FUNCTION IF EXISTS droplanguage_00182_handler;
\set ON_ERROR_STOP on
-- 2. 创建完整本地语言和因子专用夹具。
CREATE FUNCTION droplanguage_00182_handler() RETURNS void AS $$ BEGIN END; $$ LANGUAGE plpgsql;
CREATE LANGUAGE droplanguage_00182_lang HANDLER droplanguage_00182_handler;
-- 3. 执行唯一获得覆盖信用的 DROP LANGUAGE。
-- primary-target-begin
DROP LANGUAGE droplanguage_00182_lang CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS language_absent FROM pg_catalog.pg_language WHERE lanname = 'droplanguage_00182_lang' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP LANGUAGE IF EXISTS droplanguage_00182_lang CASCADE;
DROP FUNCTION IF EXISTS droplanguage_00182_handler;
