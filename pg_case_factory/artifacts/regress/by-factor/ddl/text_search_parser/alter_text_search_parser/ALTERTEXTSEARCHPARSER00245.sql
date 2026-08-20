-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TEXT SEARCH PARSER target_action=set_schema
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTEXTSEARCHPARSER00245
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_parser/alter_text_search_parser.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_parser/alter_text_search_parser.yaml
-- primary_obligation_id: ATSP-EXT|00245|catalog_query_pg_ts_parser|drop_text_search_parser
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH PARSER IF EXISTS alter_text_search_parser_00245_parser_schema.alter_text_search_parser_00245_parser CASCADE;
DROP SCHEMA IF EXISTS alter_text_search_parser_00245_parser_schema CASCADE;
DROP SCHEMA IF EXISTS alter_text_search_parser_00245_tgt_schema CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA alter_text_search_parser_00245_parser_schema;
CREATE SCHEMA alter_text_search_parser_00245_tgt_schema;
CREATE TEXT SEARCH PARSER alter_text_search_parser_00245_parser_schema.alter_text_search_parser_00245_parser (START = prsd_start, GETTOKEN = prsd_nexttoken, END = prsd_end, LEXTYPES = prsd_lextype, HEADLINE = prsd_headline);
-- 3. 执行唯一获得覆盖信用的 ALTER TEXT SEARCH PARSER。
-- primary-target-begin
ALTER TEXT SEARCH PARSER alter_text_search_parser_00245_parser_schema.alter_text_search_parser_00245_parser SET SCHEMA alter_text_search_parser_00245_tgt_schema;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS parser_state FROM pg_catalog.pg_ts_parser WHERE prsname = 'alter_text_search_parser_00245_parser' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TEXT SEARCH PARSER IF EXISTS alter_text_search_parser_00245_parser_schema.alter_text_search_parser_00245_parser CASCADE;
DROP SCHEMA IF EXISTS alter_text_search_parser_00245_parser_schema CASCADE;
DROP SCHEMA IF EXISTS alter_text_search_parser_00245_tgt_schema CASCADE;
