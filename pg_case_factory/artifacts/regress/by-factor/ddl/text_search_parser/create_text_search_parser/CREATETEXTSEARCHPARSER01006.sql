-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TEXT SEARCH PARSER privilege_level=non_superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETEXTSEARCHPARSER01006
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_parser/create_text_search_parser.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_parser/create_text_search_parser.yaml
-- primary_obligation_id: CTSP-EXT|01006|error_assertion|drop_function|headline_fn_dep
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH PARSER IF EXISTS createtextsearchparser_01006_schema.createtextsearchparser_01006_parser;
DROP FUNCTION IF EXISTS createtextsearchparser_01006_schema.createtextsearchparser_01006_start(internal) CASCADE;
DROP FUNCTION IF EXISTS createtextsearchparser_01006_schema.createtextsearchparser_01006_gettoken(internal) CASCADE;
DROP FUNCTION IF EXISTS createtextsearchparser_01006_schema.createtextsearchparser_01006_end(internal) CASCADE;
DROP FUNCTION IF EXISTS createtextsearchparser_01006_schema.createtextsearchparser_01006_lextypes(internal) CASCADE;
DROP FUNCTION IF EXISTS createtextsearchparser_01006_schema.createtextsearchparser_01006_headline(internal) CASCADE;
DROP SCHEMA IF EXISTS createtextsearchparser_01006_schema CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createtextsearchparser_01006_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createtextsearchparser_01006_schema;
CREATE FUNCTION createtextsearchparser_01006_schema.createtextsearchparser_01006_start(internal) RETURNS internal AS 'dsimple' LANGUAGE C STRICT;
CREATE FUNCTION createtextsearchparser_01006_schema.createtextsearchparser_01006_gettoken(internal) RETURNS internal AS 'dsimple' LANGUAGE C STRICT;
CREATE FUNCTION createtextsearchparser_01006_schema.createtextsearchparser_01006_end(internal) RETURNS internal AS 'dsimple' LANGUAGE C STRICT;
CREATE FUNCTION createtextsearchparser_01006_schema.createtextsearchparser_01006_lextypes(internal) RETURNS internal AS 'dsimple' LANGUAGE C STRICT;
CREATE FUNCTION createtextsearchparser_01006_schema.createtextsearchparser_01006_headline(internal) RETURNS internal AS 'dsimple' LANGUAGE C STRICT;
CREATE ROLE createtextsearchparser_01006_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA createtextsearchparser_01006_schema TO createtextsearchparser_01006_actor;
SET ROLE createtextsearchparser_01006_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TEXT SEARCH PARSER。
-- primary-target-begin
CREATE TEXT SEARCH PARSER createtextsearchparser_01006_schema.createtextsearchparser_01006_parser (start_function = createtextsearchparser_01006_schema.createtextsearchparser_01006_start, gettoken_function = createtextsearchparser_01006_schema.createtextsearchparser_01006_gettoken, end_function = createtextsearchparser_01006_schema.createtextsearchparser_01006_end, lextypes_function = createtextsearchparser_01006_schema.createtextsearchparser_01006_lextypes, headline_function = createtextsearchparser_01006_schema.createtextsearchparser_01006_headline);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION IF EXISTS createtextsearchparser_01006_schema.createtextsearchparser_01006_start(internal) CASCADE;
DROP FUNCTION IF EXISTS createtextsearchparser_01006_schema.createtextsearchparser_01006_gettoken(internal) CASCADE;
DROP FUNCTION IF EXISTS createtextsearchparser_01006_schema.createtextsearchparser_01006_end(internal) CASCADE;
DROP FUNCTION IF EXISTS createtextsearchparser_01006_schema.createtextsearchparser_01006_lextypes(internal) CASCADE;
DROP FUNCTION IF EXISTS createtextsearchparser_01006_schema.createtextsearchparser_01006_headline(internal) CASCADE;
DROP SCHEMA IF EXISTS createtextsearchparser_01006_schema CASCADE;
DROP OWNED BY createtextsearchparser_01006_actor CASCADE;
DROP ROLE IF EXISTS createtextsearchparser_01006_actor;
