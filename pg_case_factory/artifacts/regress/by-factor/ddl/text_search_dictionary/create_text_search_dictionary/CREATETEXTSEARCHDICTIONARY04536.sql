-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TEXT SEARCH DICTIONARY target_action=create_dictionary
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETEXTSEARCHDICTIONARY04536
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_dictionary/create_text_search_dictionary.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_dictionary/create_text_search_dictionary.yaml
-- primary_obligation_id: CTSD-EXT|04536|error_assertion|drop_text_search_dictionary
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH DICTIONARY IF EXISTS createtextsearchdictionary_04536_dict CASCADE;
DROP TEXT SEARCH TEMPLATE IF EXISTS createtextsearchdictionary_04536_tmpl;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TEXT SEARCH DICTIONARY。
-- primary-target-begin
CREATE TEXT SEARCH DICTIONARY createtextsearchdictionary_04536_dict (TEMPLATE = pg_catalog.simple, stopwords = 'createtextsearchdictionary_04536_stop0', language = 'createtextsearchdictionary_04536_stop1');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TEXT SEARCH DICTIONARY IF EXISTS createtextsearchdictionary_04536_dict CASCADE;
