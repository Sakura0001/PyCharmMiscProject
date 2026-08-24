-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TEXT SEARCH DICTIONARY object_state=not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTEXTSEARCHDICTIONARY00429
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_dictionary/alter_text_search_dictionary.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_dictionary/alter_text_search_dictionary.yaml
-- primary_obligation_id: ATSD-EXT|00429|catalog_query_pg_ts_dict|role_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS residual_check_no_objects;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS target_dictionary_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TEXT SEARCH DICTIONARY。
-- primary-target-begin
ALTER TEXT SEARCH DICTIONARY alter_text_search_dictionary_00429_no_such_dict OWNER TO CURRENT_ROLE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS dict_state FROM pg_catalog.pg_ts_dict WHERE dictname = 'alter_text_search_dictionary_00429_no_such_dict' ORDER BY count(*);
-- 5. 清理全部本编号对象。
SELECT 1 AS residual_check_no_objects;
