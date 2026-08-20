-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TEXT SEARCH DICTIONARY template_existence=template_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETEXTSEARCHDICTIONARY04178
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_dictionary/create_text_search_dictionary.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_dictionary/create_text_search_dictionary.yaml
-- primary_obligation_id: CTSD-EXT|04178|catalog_query_pg_ts_dict|drop_text_search_dictionary
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH DICTIONARY IF EXISTS createtextsearchdictionary_04178_dict CASCADE;
DROP TEXT SEARCH TEMPLATE IF EXISTS createtextsearchdictionary_04178_tmpl;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TEXT SEARCH DICTIONARY。
-- primary-target-begin
CREATE TEXT SEARCH DICTIONARY createtextsearchdictionary_04178_dict (TEMPLATE = createtextsearchdictionary_04178_nosuchtmpl, stopwords = 'createtextsearchdictionary_04178_stop0', language = 'createtextsearchdictionary_04178_stop1');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS dict_state FROM pg_catalog.pg_ts_dict WHERE dictname = 'createtextsearchdictionary_04178_dict' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TEXT SEARCH DICTIONARY IF EXISTS createtextsearchdictionary_04178_dict CASCADE;
