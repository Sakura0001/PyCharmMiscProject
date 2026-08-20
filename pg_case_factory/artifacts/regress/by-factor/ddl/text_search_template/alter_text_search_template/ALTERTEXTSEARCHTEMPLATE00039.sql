-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TEXT SEARCH TEMPLATE privilege_level=non_superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTEXTSEARCHTEMPLATE00039
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_template/alter_text_search_template.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_template/alter_text_search_template.yaml
-- primary_obligation_id: ATST-EXT|00039|error_assertion|drop_text_search_template
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH TEMPLATE IF EXISTS "altertextsearchtemplate_00039_Mixed Tmpl";
DROP TEXT SEARCH TEMPLATE IF EXISTS "altertextsearchtemplate_00039_Mixed New";
DROP OWNED BY altertextsearchtemplate_00039_actor CASCADE;
DROP ROLE IF EXISTS altertextsearchtemplate_00039_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE altertextsearchtemplate_00039_actor LOGIN NOSUPERUSER;
CREATE TEXT SEARCH TEMPLATE "altertextsearchtemplate_00039_Mixed Tmpl" (lexize = dsimple_lexize);
SET ROLE altertextsearchtemplate_00039_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TEXT SEARCH TEMPLATE。
-- primary-target-begin
ALTER TEXT SEARCH TEMPLATE "altertextsearchtemplate_00039_Mixed Tmpl" RENAME TO "altertextsearchtemplate_00039_Mixed New";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TEXT SEARCH TEMPLATE IF EXISTS "altertextsearchtemplate_00039_Mixed Tmpl";
DROP TEXT SEARCH TEMPLATE IF EXISTS "altertextsearchtemplate_00039_Mixed New";
DROP OWNED BY altertextsearchtemplate_00039_actor CASCADE;
DROP ROLE IF EXISTS altertextsearchtemplate_00039_actor;
