-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TEXT SEARCH DICTIONARY if_exists_clause=present
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTEXTSEARCHDICTIONARY00026
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_dictionary/drop_text_search_dictionary.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_dictionary/drop_text_search_dictionary.yaml
-- primary_obligation_id: DROPTEXTSEARCHDICTIONARY-SFV|sfv-1654783e68bbefd8327f21ec|drop_text_search_dictionary
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH DICTIONARY IF EXISTS droptextsearchdictionary_00026_dict CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地字典和因子专用夹具。
CREATE TEXT SEARCH DICTIONARY droptextsearchdictionary_00026_dict (TEMPLATE = simple);
-- 3. 执行唯一获得覆盖信用的 DROP TEXT SEARCH DICTIONARY。
-- primary-target-begin
DROP TEXT SEARCH DICTIONARY IF EXISTS droptextsearchdictionary_00026_dict;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS dict_absent FROM pg_catalog.pg_ts_dict WHERE dictname = 'droptextsearchdictionary_00026_dict' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TEXT SEARCH DICTIONARY IF EXISTS droptextsearchdictionary_00026_dict CASCADE;
