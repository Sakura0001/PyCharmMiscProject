-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TEXT SEARCH PARSER parser_name_shape=reserved_word_as_name
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETEXTSEARCHPARSER00952
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_parser/create_text_search_parser.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_parser/create_text_search_parser.yaml
-- primary_obligation_id: CTSP-EXT|00952|catalog_query_pg_ts_parser|drop_function|parser_dependency
-- expected_outcome: expected_failure
-- expected_sqlstate: 42601
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS createtextsearchparser_00952_schema.createtextsearchparser_00952_start(internal) CASCADE;
DROP FUNCTION IF EXISTS createtextsearchparser_00952_schema.createtextsearchparser_00952_gettoken(internal) CASCADE;
DROP FUNCTION IF EXISTS createtextsearchparser_00952_schema.createtextsearchparser_00952_end(internal) CASCADE;
DROP FUNCTION IF EXISTS createtextsearchparser_00952_schema.createtextsearchparser_00952_lextypes(internal) CASCADE;
DROP FUNCTION IF EXISTS createtextsearchparser_00952_schema.createtextsearchparser_00952_headline(internal) CASCADE;
DROP SCHEMA IF EXISTS createtextsearchparser_00952_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createtextsearchparser_00952_schema;
CREATE FUNCTION createtextsearchparser_00952_schema.createtextsearchparser_00952_start(internal) RETURNS internal AS 'dsimple' LANGUAGE C STRICT;
CREATE FUNCTION createtextsearchparser_00952_schema.createtextsearchparser_00952_gettoken(internal) RETURNS internal AS 'dsimple' LANGUAGE C STRICT;
CREATE FUNCTION createtextsearchparser_00952_schema.createtextsearchparser_00952_end(internal) RETURNS internal AS 'dsimple' LANGUAGE C STRICT;
CREATE FUNCTION createtextsearchparser_00952_schema.createtextsearchparser_00952_lextypes(internal) RETURNS internal AS 'dsimple' LANGUAGE C STRICT;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TEXT SEARCH PARSER。
-- primary-target-begin
CREATE TEXT SEARCH PARSER select (start_function = createtextsearchparser_00952_schema.createtextsearchparser_00952_start, gettoken_function = createtextsearchparser_00952_schema.createtextsearchparser_00952_gettoken, end_function = createtextsearchparser_00952_schema.createtextsearchparser_00952_end, lextypes_function = createtextsearchparser_00952_schema.createtextsearchparser_00952_lextypes);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42601' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS parser_state FROM pg_catalog.pg_ts_parser WHERE prsname = 'select' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP FUNCTION IF EXISTS createtextsearchparser_00952_schema.createtextsearchparser_00952_start(internal) CASCADE;
DROP FUNCTION IF EXISTS createtextsearchparser_00952_schema.createtextsearchparser_00952_gettoken(internal) CASCADE;
DROP FUNCTION IF EXISTS createtextsearchparser_00952_schema.createtextsearchparser_00952_end(internal) CASCADE;
DROP FUNCTION IF EXISTS createtextsearchparser_00952_schema.createtextsearchparser_00952_lextypes(internal) CASCADE;
DROP SCHEMA IF EXISTS createtextsearchparser_00952_schema CASCADE;
