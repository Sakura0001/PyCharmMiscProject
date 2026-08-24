-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TEXT SEARCH TEMPLATE schema_name_shape=nonexistent_schema
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTEXTSEARCHTEMPLATE00149
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_template/alter_text_search_template.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_template/alter_text_search_template.yaml
-- primary_obligation_id: ATST-EXT|00149|catalog_query_pg_ts_template|drop_text_search_template
-- expected_outcome: expected_failure
-- expected_sqlstate: 3F000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH TEMPLATE IF EXISTS altertextsearchtemplate_00149_tmpl;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TEXT SEARCH TEMPLATE altertextsearchtemplate_00149_tmpl (lexize = dsimple_lexize);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TEXT SEARCH TEMPLATE。
-- primary-target-begin
ALTER TEXT SEARCH TEMPLATE altertextsearchtemplate_00149_tmpl SET SCHEMA altertextsearchtemplate_00149_no_such_sch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '3F000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS template_state FROM pg_catalog.pg_ts_template WHERE tmplname = 'altertextsearchtemplate_00149_tmpl' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TEXT SEARCH TEMPLATE IF EXISTS altertextsearchtemplate_00149_tmpl;
