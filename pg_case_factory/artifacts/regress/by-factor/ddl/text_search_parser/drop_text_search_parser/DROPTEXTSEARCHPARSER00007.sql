-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TEXT SEARCH PARSER dependency_context=config_using_parser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTEXTSEARCHPARSER00007
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_parser/drop_text_search_parser.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_parser/drop_text_search_parser.yaml
-- primary_obligation_id: DROPTEXTSEARCHPARSER-SFV|sfv-b4a8b1734750798b0de28e8c|drop_text_search_parser
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH CONFIGURATION IF EXISTS droptextsearchparser_00007_config CASCADE;
DROP TEXT SEARCH PARSER IF EXISTS droptextsearchparser_00007_parser CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地解析器和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE TEXT SEARCH PARSER droptextsearchparser_00007_parser ( START = prsd_start, GETTOKEN = prsd_nexttoken, END = prsd_end, LEXTYPES = prsd_lextype, HEADLINE = prsd_headline);
CREATE TEXT SEARCH CONFIGURATION droptextsearchparser_00007_config (PARSER = droptextsearchparser_00007_parser);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TEXT SEARCH PARSER。
-- primary-target-begin
DROP TEXT SEARCH PARSER IF EXISTS droptextsearchparser_00007_parser;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS parser_present FROM pg_catalog.pg_ts_parser WHERE prsname = 'droptextsearchparser_00007_parser' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TEXT SEARCH CONFIGURATION IF EXISTS droptextsearchparser_00007_config CASCADE;
DROP TEXT SEARCH PARSER IF EXISTS droptextsearchparser_00007_parser CASCADE;
