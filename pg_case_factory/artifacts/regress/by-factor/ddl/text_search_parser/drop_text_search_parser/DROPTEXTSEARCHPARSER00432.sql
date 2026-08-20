-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TEXT SEARCH PARSER privilege_requirement=non_superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTEXTSEARCHPARSER00432
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_parser/drop_text_search_parser.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_parser/drop_text_search_parser.yaml
-- primary_obligation_id: DROPTEXTSEARCHPARSER-EXT|00432|drop_text_search_parser|notice_assertion|manual_dependency_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH CONFIGURATION IF EXISTS droptextsearchparser_00432_config CASCADE;
DROP TEXT SEARCH PARSER IF EXISTS "user" CASCADE;
DROP OWNED BY droptextsearchparser_00432_actor;
DROP ROLE IF EXISTS droptextsearchparser_00432_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地解析器和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE ROLE droptextsearchparser_00432_actor LOGIN NOSUPERUSER;
CREATE TEXT SEARCH PARSER "user" ( START = prsd_start, GETTOKEN = prsd_nexttoken, END = prsd_end, LEXTYPES = prsd_lextype, HEADLINE = prsd_headline);
CREATE TEXT SEARCH CONFIGURATION droptextsearchparser_00432_config (PARSER = "user");
SET ROLE droptextsearchparser_00432_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TEXT SEARCH PARSER。
-- primary-target-begin
DROP TEXT SEARCH PARSER IF EXISTS "user" CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS parser_present FROM pg_catalog.pg_ts_parser WHERE prsname = 'user' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TEXT SEARCH CONFIGURATION IF EXISTS droptextsearchparser_00432_config CASCADE;
DROP TEXT SEARCH PARSER IF EXISTS "user" CASCADE;
DROP OWNED BY droptextsearchparser_00432_actor;
DROP ROLE IF EXISTS droptextsearchparser_00432_actor;
