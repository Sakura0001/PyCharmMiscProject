-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TEXT SEARCH DICTIONARY privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTEXTSEARCHDICTIONARY00575
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_dictionary/alter_text_search_dictionary.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_dictionary/alter_text_search_dictionary.yaml
-- primary_obligation_id: ATSD-EXT|00575|catalog_query_pg_ts_dict|revert_option
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH DICTIONARY IF EXISTS alter_text_search_dictionary_00575_dict;
DROP OWNED BY alter_text_search_dictionary_00575_actor CASCADE;
DROP ROLE IF EXISTS alter_text_search_dictionary_00575_actor;
DROP OWNED BY alter_text_search_dictionary_00575_newowner CASCADE;
DROP ROLE IF EXISTS alter_text_search_dictionary_00575_newowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alter_text_search_dictionary_00575_actor LOGIN NOSUPERUSER;
CREATE ROLE alter_text_search_dictionary_00575_newowner LOGIN;
CREATE TEXT SEARCH DICTIONARY alter_text_search_dictionary_00575_dict (TEMPLATE = pg_catalog.simple);
SET ROLE alter_text_search_dictionary_00575_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TEXT SEARCH DICTIONARY。
-- primary-target-begin
ALTER TEXT SEARCH DICTIONARY "alter_text_search_dictionary_00575_Mixed Dict" OWNER TO alter_text_search_dictionary_00575_newowner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS dict_state FROM pg_catalog.pg_ts_dict WHERE dictname = 'alter_text_search_dictionary_00575_Mixed Dict' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TEXT SEARCH DICTIONARY IF EXISTS alter_text_search_dictionary_00575_dict;
DROP OWNED BY alter_text_search_dictionary_00575_actor CASCADE;
DROP ROLE IF EXISTS alter_text_search_dictionary_00575_actor;
DROP OWNED BY alter_text_search_dictionary_00575_newowner CASCADE;
DROP ROLE IF EXISTS alter_text_search_dictionary_00575_newowner;
