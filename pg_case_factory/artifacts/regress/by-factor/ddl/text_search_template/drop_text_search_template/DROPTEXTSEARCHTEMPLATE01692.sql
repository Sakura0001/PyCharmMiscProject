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
-- case_id: DROPTEXTSEARCHTEMPLATE01692
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_template/drop_text_search_template.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_template/drop_text_search_template.yaml
-- primary_obligation_id: DROPTEXTSEARCHTEMPLATE-EXT|01692|drop_text_search_template|notice_assertion|manual_dependency_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH TEMPLATE IF EXISTS droptextsearchtemplate_01692_noexist CASCADE;
DROP OWNED BY droptextsearchtemplate_01692_actor;
DROP ROLE IF EXISTS droptextsearchtemplate_01692_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地模板和因子专用夹具。
CREATE ROLE droptextsearchtemplate_01692_actor LOGIN NOSUPERUSER;
SELECT 1 AS target_template_intentionally_absent;
SET ROLE droptextsearchtemplate_01692_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TEXT SEARCH TEMPLATE。
-- primary-target-begin
DROP TEXT SEARCH TEMPLATE IF EXISTS droptextsearchtemplate_01692_noexist CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS template_absent FROM pg_catalog.pg_ts_template WHERE tmplname = 'droptextsearchtemplate_01692_noexist' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TEXT SEARCH TEMPLATE IF EXISTS droptextsearchtemplate_01692_noexist CASCADE;
DROP OWNED BY droptextsearchtemplate_01692_actor;
DROP ROLE IF EXISTS droptextsearchtemplate_01692_actor;
