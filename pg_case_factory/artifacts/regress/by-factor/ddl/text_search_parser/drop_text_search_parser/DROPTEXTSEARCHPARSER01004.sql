-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TEXT SEARCH PARSER object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTEXTSEARCHPARSER01004
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_parser/drop_text_search_parser.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_parser/drop_text_search_parser.yaml
-- primary_obligation_id: DROPTEXTSEARCHPARSER-EXT|01004|drop_text_search_parser|catalog_query|manual_dependency_cleanup
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH PARSER IF EXISTS "user" CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地解析器和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE TEXT SEARCH PARSER "user" ( START = prsd_start, GETTOKEN = prsd_nexttoken, END = prsd_end, LEXTYPES = prsd_lextype, HEADLINE = prsd_headline);
-- 3. 执行唯一获得覆盖信用的 DROP TEXT SEARCH PARSER。
-- primary-target-begin
DROP TEXT SEARCH PARSER IF EXISTS "user" RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS parser_absent FROM pg_catalog.pg_ts_parser WHERE prsname = 'user' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TEXT SEARCH PARSER IF EXISTS "user" CASCADE;
