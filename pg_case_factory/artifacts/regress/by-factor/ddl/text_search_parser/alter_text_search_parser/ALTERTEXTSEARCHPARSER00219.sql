-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TEXT SEARCH PARSER nonexistent_target_schema=schema_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTEXTSEARCHPARSER00219
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_parser/alter_text_search_parser.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_parser/alter_text_search_parser.yaml
-- primary_obligation_id: ATSP-EXT|00219|error_assertion|drop_text_search_parser
-- expected_outcome: expected_failure
-- expected_sqlstate: 3F000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH PARSER IF EXISTS alter_text_search_parser_00219_parser CASCADE;
DROP SCHEMA IF EXISTS alter_text_search_parser_00219_no_such_schema CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TEXT SEARCH PARSER alter_text_search_parser_00219_parser (START = prsd_start, GETTOKEN = prsd_nexttoken, END = prsd_end, LEXTYPES = prsd_lextype, HEADLINE = prsd_headline);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TEXT SEARCH PARSER。
-- primary-target-begin
ALTER TEXT SEARCH PARSER alter_text_search_parser_00219_parser SET SCHEMA alter_text_search_parser_00219_no_such_schema;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '3F000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TEXT SEARCH PARSER IF EXISTS alter_text_search_parser_00219_parser CASCADE;
DROP SCHEMA IF EXISTS alter_text_search_parser_00219_no_such_schema CASCADE;
