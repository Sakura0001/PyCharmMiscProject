-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TEXT SEARCH TEMPLATE dependency_context=dict_using_template
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTEXTSEARCHTEMPLATE00425
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_template/drop_text_search_template.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_template/drop_text_search_template.yaml
-- primary_obligation_id: DROPTEXTSEARCHTEMPLATE-EXT|00425|drop_text_search_template|notice_assertion|cascade_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH DICTIONARY IF EXISTS droptextsearchtemplate_00425_dict CASCADE;
DROP TEXT SEARCH TEMPLATE IF EXISTS "droptextsearchtemplate_00425_qtmpl" CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地模板和因子专用夹具。
CREATE TEXT SEARCH TEMPLATE "droptextsearchtemplate_00425_qtmpl" INIT (dsimple_init) LEXIZE (dsimple_lexize);
CREATE TEXT SEARCH DICTIONARY droptextsearchtemplate_00425_dict TEMPLATE "droptextsearchtemplate_00425_qtmpl";
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TEXT SEARCH TEMPLATE。
-- primary-target-begin
DROP TEXT SEARCH TEMPLATE IF EXISTS "droptextsearchtemplate_00425_qtmpl";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS template_present FROM pg_catalog.pg_ts_template WHERE tmplname = 'droptextsearchtemplate_00425_qtmpl' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TEXT SEARCH DICTIONARY IF EXISTS droptextsearchtemplate_00425_dict CASCADE;
DROP TEXT SEARCH TEMPLATE IF EXISTS "droptextsearchtemplate_00425_qtmpl" CASCADE;
