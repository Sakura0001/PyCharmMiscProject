-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TEXT SEARCH DICTIONARY authorization_path=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTEXTSEARCHDICTIONARY00334
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_dictionary/drop_text_search_dictionary.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_dictionary/drop_text_search_dictionary.yaml
-- primary_obligation_id: DROPTEXTSEARCHDICTIONARY-EXT|00334|drop_text_search_dictionary|catalog_query|manual_dependency_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH DICTIONARY IF EXISTS droptextsearchdictionary_00334_nodict CASCADE;
DROP OWNED BY droptextsearchdictionary_00334_actor;
DROP ROLE IF EXISTS droptextsearchdictionary_00334_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地字典和因子专用夹具。
CREATE ROLE droptextsearchdictionary_00334_actor LOGIN NOSUPERUSER;
SET ROLE droptextsearchdictionary_00334_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TEXT SEARCH DICTIONARY。
-- primary-target-begin
DROP TEXT SEARCH DICTIONARY IF EXISTS droptextsearchdictionary_00334_nodict RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS dict_absent FROM pg_catalog.pg_ts_dict WHERE dictname = 'droptextsearchdictionary_00334_nodict' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TEXT SEARCH DICTIONARY IF EXISTS droptextsearchdictionary_00334_nodict CASCADE;
DROP OWNED BY droptextsearchdictionary_00334_actor;
DROP ROLE IF EXISTS droptextsearchdictionary_00334_actor;
