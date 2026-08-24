-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TEXT SEARCH TEMPLATE privilege_requirement=non_superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTEXTSEARCHTEMPLATE03277
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_template/drop_text_search_template.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_template/drop_text_search_template.yaml
-- primary_obligation_id: DROPTEXTSEARCHTEMPLATE-EXT|03277|drop_text_search_template|catalog_query|cascade_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH TEMPLATE IF EXISTS "select" CASCADE;
DROP OWNED BY droptextsearchtemplate_03277_actor;
DROP ROLE IF EXISTS droptextsearchtemplate_03277_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地模板和因子专用夹具。
CREATE ROLE droptextsearchtemplate_03277_actor LOGIN NOSUPERUSER;
CREATE TEXT SEARCH TEMPLATE "select" INIT (dsimple_init) LEXIZE (dsimple_lexize);
SET ROLE droptextsearchtemplate_03277_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TEXT SEARCH TEMPLATE。
-- primary-target-begin
DROP TEXT SEARCH TEMPLATE "select" RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS template_present FROM pg_catalog.pg_ts_template WHERE tmplname = 'select' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TEXT SEARCH TEMPLATE IF EXISTS "select" CASCADE;
DROP OWNED BY droptextsearchtemplate_03277_actor;
DROP ROLE IF EXISTS droptextsearchtemplate_03277_actor;
