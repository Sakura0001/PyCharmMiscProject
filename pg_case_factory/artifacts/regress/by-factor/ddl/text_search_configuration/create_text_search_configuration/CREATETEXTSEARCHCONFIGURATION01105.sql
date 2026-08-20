-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TEXT SEARCH CONFIGURATION target_action=copy
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETEXTSEARCHCONFIGURATION01105
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_configuration/create_text_search_configuration.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_configuration/create_text_search_configuration.yaml
-- primary_obligation_id: CTSC-EXT|01105|error_assertion|drop_text_search_configuration
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH CONFIGURATION IF EXISTS createtextsearchconfiguration_01105_cfg CASCADE;
DROP TEXT SEARCH CONFIGURATION IF EXISTS public.createtextsearchconfiguration_01105_cfg CASCADE;
DROP TEXT SEARCH CONFIGURATION IF EXISTS "createtextsearchconfiguration_01105_qcfg" CASCADE;
DROP TEXT SEARCH CONFIGURATION IF EXISTS createtextsearchconfiguration_01105_srccfg CASCADE;
DROP TEXT SEARCH PARSER IF EXISTS createtextsearchconfiguration_01105_custparser CASCADE;
DROP SCHEMA IF EXISTS createtextsearchconfiguration_01105_nosuchschema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TEXT SEARCH CONFIGURATION "createtextsearchconfiguration_01105_qsrccfg" (PARSER = default);
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信度的 CREATE TEXT SEARCH CONFIGURATION。
-- primary-target-begin
CREATE TEXT SEARCH CONFIGURATION createtextsearchconfiguration_01105_cfg (COPY = "createtextsearchconfiguration_01105_qsrccfg");
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TEXT SEARCH CONFIGURATION IF EXISTS createtextsearchconfiguration_01105_cfg;
DROP TEXT SEARCH CONFIGURATION IF EXISTS "createtextsearchconfiguration_01105_qsrccfg";
