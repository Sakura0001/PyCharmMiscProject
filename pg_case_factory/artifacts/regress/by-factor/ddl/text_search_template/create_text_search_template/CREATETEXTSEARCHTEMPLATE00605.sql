-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TEXT SEARCH TEMPLATE privilege_level=non_superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETEXTSEARCHTEMPLATE00605
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_template/create_text_search_template.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_template/create_text_search_template.yaml
-- primary_obligation_id: CTST-EXT|00605|error_assertion|drop_text_search_template|statement_fn_dep
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH TEMPLATE IF EXISTS createtextsearchtemplate_00605_schema.createtextsearchtemplate_00605_template;
DROP FUNCTION IF EXISTS createtextsearchtemplate_00605_schema.createtextsearchtemplate_00605_lexize(internal) CASCADE;
DROP FUNCTION IF EXISTS createtextsearchtemplate_00605_schema.createtextsearchtemplate_00605_init(internal) CASCADE;
DROP SCHEMA IF EXISTS createtextsearchtemplate_00605_schema CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createtextsearchtemplate_00605_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createtextsearchtemplate_00605_schema;
CREATE FUNCTION createtextsearchtemplate_00605_schema.createtextsearchtemplate_00605_lexize(internal) RETURNS internal AS 'dsimple' LANGUAGE C STRICT;
CREATE FUNCTION createtextsearchtemplate_00605_schema.createtextsearchtemplate_00605_init(internal) RETURNS internal AS 'dsimple' LANGUAGE C STRICT;
CREATE ROLE createtextsearchtemplate_00605_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA createtextsearchtemplate_00605_schema TO createtextsearchtemplate_00605_actor;
SET ROLE createtextsearchtemplate_00605_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TEXT SEARCH TEMPLATE。
-- primary-target-begin
CREATE TEXT SEARCH TEMPLATE createtextsearchtemplate_00605_schema.createtextsearchtemplate_00605_template (lexize = createtextsearchtemplate_00605_schema.createtextsearchtemplate_00605_lexize, init = createtextsearchtemplate_00605_schema.createtextsearchtemplate_00605_init);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TEXT SEARCH TEMPLATE IF EXISTS createtextsearchtemplate_00605_schema.createtextsearchtemplate_00605_template;
DROP FUNCTION IF EXISTS createtextsearchtemplate_00605_schema.createtextsearchtemplate_00605_lexize(internal) CASCADE;
DROP FUNCTION IF EXISTS createtextsearchtemplate_00605_schema.createtextsearchtemplate_00605_init(internal) CASCADE;
DROP SCHEMA IF EXISTS createtextsearchtemplate_00605_schema CASCADE;
DROP OWNED BY createtextsearchtemplate_00605_actor CASCADE;
DROP ROLE IF EXISTS createtextsearchtemplate_00605_actor;
