-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TEXT SEARCH TEMPLATE template_name_shape=simple_id
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTEXTSEARCHTEMPLATE00033
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_template/alter_text_search_template.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_template/alter_text_search_template.yaml
-- primary_obligation_id: ATST-SFV|sfv-b041e8c2cd23128b8422c6d1|rename
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH TEMPLATE IF EXISTS altertextsearchtemplate_00033_tmpl;
DROP TEXT SEARCH TEMPLATE IF EXISTS altertextsearchtemplate_00033_newtmpl;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TEXT SEARCH TEMPLATE altertextsearchtemplate_00033_tmpl (lexize = dsimple_lexize);
-- 3. 执行唯一获得覆盖信用的 ALTER TEXT SEARCH TEMPLATE。
-- primary-target-begin
ALTER TEXT SEARCH TEMPLATE altertextsearchtemplate_00033_tmpl RENAME TO altertextsearchtemplate_00033_newtmpl;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS template_state FROM pg_catalog.pg_ts_template WHERE tmplname = 'altertextsearchtemplate_00033_newtmpl' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TEXT SEARCH TEMPLATE IF EXISTS altertextsearchtemplate_00033_tmpl;
DROP TEXT SEARCH TEMPLATE IF EXISTS altertextsearchtemplate_00033_newtmpl;
