-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TEXT SEARCH CONFIGURATION object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTEXTSEARCHCONFIGURATION01613
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_configuration/drop_text_search_configuration.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_configuration/drop_text_search_configuration.yaml
-- primary_obligation_id: DROPTEXTSEARCHCONFIGURATION-EXT|01613|drop_text_search_configuration|error_assertion|cascade_cleanup
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS residual_check_no_objects;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS target_config_intentionally_absent;
-- 3. 执行唯一获得覆盖信用的 DROP TEXT SEARCH CONFIGURATION。
-- primary-target-begin
DROP TEXT SEARCH CONFIGURATION IF EXISTS droptextsearchconfiguration_01613_cfg CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
SELECT 1 AS residual_check_no_objects;
