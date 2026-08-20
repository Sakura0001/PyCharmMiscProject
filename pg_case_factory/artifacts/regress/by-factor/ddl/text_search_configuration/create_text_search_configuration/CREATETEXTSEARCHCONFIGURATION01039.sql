-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TEXT SEARCH CONFIGURATION parser_existence=parser_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETEXTSEARCHCONFIGURATION01039
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_configuration/create_text_search_configuration.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_configuration/create_text_search_configuration.yaml
-- primary_obligation_id: CTSC-EXT|01039|catalog_query_pg_ts_config|drop_text_search_configuration
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH CONFIGURATION IF EXISTS createtextsearchconfiguration_01039_cfg CASCADE;
DROP TEXT SEARCH CONFIGURATION IF EXISTS public.createtextsearchconfiguration_01039_cfg CASCADE;
DROP TEXT SEARCH CONFIGURATION IF EXISTS "createtextsearchconfiguration_01039_qcfg" CASCADE;
DROP TEXT SEARCH CONFIGURATION IF EXISTS createtextsearchconfiguration_01039_srccfg CASCADE;
DROP TEXT SEARCH PARSER IF EXISTS createtextsearchconfiguration_01039_custparser CASCADE;
DROP SCHEMA IF EXISTS createtextsearchconfiguration_01039_nosuchschema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信度的 CREATE TEXT SEARCH CONFIGURATION。
-- primary-target-begin
CREATE TEXT SEARCH CONFIGURATION public.createtextsearchconfiguration_01039_cfg (PARSER = createtextsearchconfiguration_01039_nosuchparser);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS config_state FROM pg_catalog.pg_ts_config WHERE cfgname = 'createtextsearchconfiguration_01039_cfg' ORDER BY count(*);
-- 5. 清理全部本编号对象。
SELECT 1 AS residual_check_no_objects;
