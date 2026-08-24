-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TEXT SEARCH DICTIONARY target_action=owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTEXTSEARCHDICTIONARY00719
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_dictionary/alter_text_search_dictionary.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_dictionary/alter_text_search_dictionary.yaml
-- primary_obligation_id: ATSD-EXT|00719|option_query|role_cleanup
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH DICTIONARY IF EXISTS alter_text_search_dictionary_00719_dict;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TEXT SEARCH DICTIONARY alter_text_search_dictionary_00719_dict (TEMPLATE = pg_catalog.simple);
-- 3. 执行唯一获得覆盖信用的 ALTER TEXT SEARCH DICTIONARY。
-- primary-target-begin
ALTER TEXT SEARCH DICTIONARY "alter_text_search_dictionary_00719_Mixed Dict" OWNER TO SESSION_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS option_state FROM pg_catalog.pg_ts_dict WHERE dictname = 'alter_text_search_dictionary_00719_Mixed Dict' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TEXT SEARCH DICTIONARY IF EXISTS alter_text_search_dictionary_00719_dict;
