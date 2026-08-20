-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TEXT SEARCH CONFIGURATION missing_parser_or_copy=none_specified
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETEXTSEARCHCONFIGURATION00756
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_configuration/create_text_search_configuration.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_configuration/create_text_search_configuration.yaml
-- primary_obligation_id: CTSC-EXT|00756|catalog_query_pg_ts_config|drop_parser
-- expected_outcome: expected_failure
-- expected_sqlstate: 42601
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH CONFIGURATION IF EXISTS createtextsearchconfiguration_00756_cfg CASCADE;
DROP TEXT SEARCH CONFIGURATION IF EXISTS public.createtextsearchconfiguration_00756_cfg CASCADE;
DROP TEXT SEARCH CONFIGURATION IF EXISTS "createtextsearchconfiguration_00756_qcfg" CASCADE;
DROP TEXT SEARCH CONFIGURATION IF EXISTS createtextsearchconfiguration_00756_srccfg CASCADE;
DROP TEXT SEARCH PARSER IF EXISTS createtextsearchconfiguration_00756_custparser CASCADE;
DROP SCHEMA IF EXISTS createtextsearchconfiguration_00756_nosuchschema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信度的 CREATE TEXT SEARCH CONFIGURATION。
-- primary-target-begin
CREATE TEXT SEARCH CONFIGURATION "createtextsearchconfiguration_00756_select" ();
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42601' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS config_state FROM pg_catalog.pg_ts_config WHERE cfgname = 'createtextsearchconfiguration_00756_select' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TEXT SEARCH PARSER IF EXISTS createtextsearchconfiguration_00756_custparser;
