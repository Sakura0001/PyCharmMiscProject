-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TEXT SEARCH PARSER privilege_level=non_superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTEXTSEARCHPARSER00073
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_parser/alter_text_search_parser.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_parser/alter_text_search_parser.yaml
-- primary_obligation_id: ATSP-EXT|00073|catalog_query_pg_ts_parser|drop_text_search_parser
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH PARSER IF EXISTS alter_text_search_parser_00073_parser_schema.alter_text_search_parser_00073_parser CASCADE;
DROP TEXT SEARCH PARSER IF EXISTS alter_text_search_parser_00073_newparser CASCADE;
DROP SCHEMA IF EXISTS alter_text_search_parser_00073_parser_schema CASCADE;
DROP OWNED BY alter_text_search_parser_00073_actor CASCADE;
DROP ROLE IF EXISTS alter_text_search_parser_00073_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alter_text_search_parser_00073_actor LOGIN NOSUPERUSER;
CREATE SCHEMA alter_text_search_parser_00073_parser_schema;
CREATE TEXT SEARCH PARSER alter_text_search_parser_00073_parser_schema.alter_text_search_parser_00073_parser (START = prsd_start, GETTOKEN = prsd_nexttoken, END = prsd_end, LEXTYPES = prsd_lextype, HEADLINE = prsd_headline);
SET ROLE alter_text_search_parser_00073_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TEXT SEARCH PARSER。
-- primary-target-begin
ALTER TEXT SEARCH PARSER alter_text_search_parser_00073_parser_schema.alter_text_search_parser_00073_parser RENAME TO alter_text_search_parser_00073_newparser;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS parser_state FROM pg_catalog.pg_ts_parser WHERE prsname = 'alter_text_search_parser_00073_parser' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TEXT SEARCH PARSER IF EXISTS alter_text_search_parser_00073_parser_schema.alter_text_search_parser_00073_parser CASCADE;
DROP TEXT SEARCH PARSER IF EXISTS alter_text_search_parser_00073_newparser CASCADE;
DROP SCHEMA IF EXISTS alter_text_search_parser_00073_parser_schema CASCADE;
DROP OWNED BY alter_text_search_parser_00073_actor CASCADE;
DROP ROLE IF EXISTS alter_text_search_parser_00073_actor;
