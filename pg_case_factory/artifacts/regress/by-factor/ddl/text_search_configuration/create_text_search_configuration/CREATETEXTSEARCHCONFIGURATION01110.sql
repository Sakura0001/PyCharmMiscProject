-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TEXT SEARCH CONFIGURATION privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETEXTSEARCHCONFIGURATION01110
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_configuration/create_text_search_configuration.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_configuration/create_text_search_configuration.yaml
-- primary_obligation_id: CTSC-EXT|01110|error_assertion|drop_parser
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH CONFIGURATION IF EXISTS createtextsearchconfiguration_01110_cfg CASCADE;
DROP TEXT SEARCH CONFIGURATION IF EXISTS public.createtextsearchconfiguration_01110_cfg CASCADE;
DROP TEXT SEARCH CONFIGURATION IF EXISTS "createtextsearchconfiguration_01110_qcfg" CASCADE;
DROP TEXT SEARCH CONFIGURATION IF EXISTS createtextsearchconfiguration_01110_srccfg CASCADE;
DROP TEXT SEARCH PARSER IF EXISTS createtextsearchconfiguration_01110_custparser CASCADE;
DROP SCHEMA IF EXISTS createtextsearchconfiguration_01110_nosuchschema CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createtextsearchconfiguration_01110_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createtextsearchconfiguration_01110_actor LOGIN NOSUPERUSER;
CREATE TEXT SEARCH CONFIGURATION public.createtextsearchconfiguration_01110_srccfg (PARSER = default);
SET ROLE createtextsearchconfiguration_01110_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信度的 CREATE TEXT SEARCH CONFIGURATION。
-- primary-target-begin
CREATE TEXT SEARCH CONFIGURATION createtextsearchconfiguration_01110_cfg (COPY = public.createtextsearchconfiguration_01110_srccfg);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TEXT SEARCH CONFIGURATION IF EXISTS public.createtextsearchconfiguration_01110_srccfg;
DROP TEXT SEARCH PARSER IF EXISTS createtextsearchconfiguration_01110_custparser;
DROP OWNED BY createtextsearchconfiguration_01110_actor CASCADE;
DROP ROLE IF EXISTS createtextsearchconfiguration_01110_actor;
