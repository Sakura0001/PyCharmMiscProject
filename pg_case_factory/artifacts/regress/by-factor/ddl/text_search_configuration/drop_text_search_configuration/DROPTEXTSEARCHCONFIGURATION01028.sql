-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TEXT SEARCH CONFIGURATION dependency_status=has_dependencies
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTEXTSEARCHCONFIGURATION01028
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_configuration/drop_text_search_configuration.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_configuration/drop_text_search_configuration.yaml
-- primary_obligation_id: DROPTEXTSEARCHCONFIGURATION-EXT|01028|drop_text_search_configuration|notice_assertion|manual_dependency_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS droptextsearchconfiguration_01028_depfn;
DROP TEXT SEARCH CONFIGURATION IF EXISTS "droptextsearchconfiguration_01028_select";
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TEXT SEARCH CONFIGURATION "droptextsearchconfiguration_01028_select" (PARSER = default);
CREATE FUNCTION droptextsearchconfiguration_01028_depfn() RETURNS tsvector LANGUAGE SQL AS $$ SELECT to_tsvector('droptextsearchconfiguration_01028_select'::regconfig, ''::text) $$;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TEXT SEARCH CONFIGURATION。
-- primary-target-begin
DROP TEXT SEARCH CONFIGURATION "droptextsearchconfiguration_01028_select" RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS config_present FROM pg_catalog.pg_ts_config WHERE cfgname = 'droptextsearchconfiguration_01028_select' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP FUNCTION IF EXISTS droptextsearchconfiguration_01028_depfn;
DROP TEXT SEARCH CONFIGURATION IF EXISTS "droptextsearchconfiguration_01028_select";
