-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TEXT SEARCH TEMPLATE object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTEXTSEARCHTEMPLATE02491
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_template/drop_text_search_template.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_template/drop_text_search_template.yaml
-- primary_obligation_id: DROPTEXTSEARCHTEMPLATE-EXT|02491|drop_text_search_template|catalog_query|cascade_cleanup
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH TEMPLATE IF EXISTS public.droptextsearchtemplate_02491_tmpl CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地模板和因子专用夹具。
SELECT 1 AS target_template_intentionally_absent;
-- 3. 执行唯一获得覆盖信用的 DROP TEXT SEARCH TEMPLATE。
-- primary-target-begin
DROP TEXT SEARCH TEMPLATE IF EXISTS public.droptextsearchtemplate_02491_tmpl CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS template_absent FROM pg_catalog.pg_ts_template WHERE tmplname = 'droptextsearchtemplate_02491_tmpl' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TEXT SEARCH TEMPLATE IF EXISTS public.droptextsearchtemplate_02491_tmpl CASCADE;
