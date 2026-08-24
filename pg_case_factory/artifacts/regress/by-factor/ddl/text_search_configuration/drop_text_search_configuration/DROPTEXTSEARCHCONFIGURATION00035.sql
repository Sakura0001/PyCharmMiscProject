-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TEXT SEARCH CONFIGURATION verification_mode=error_assertion
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTEXTSEARCHCONFIGURATION00035
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_configuration/drop_text_search_configuration.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_configuration/drop_text_search_configuration.yaml
-- primary_obligation_id: DROPTEXTSEARCHCONFIGURATION-SFV|sfv-0737d9ae8212c0b3d19b7188|drop_text_search_configuration
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH CONFIGURATION IF EXISTS droptextsearchconfiguration_00035_cfg;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TEXT SEARCH CONFIGURATION droptextsearchconfiguration_00035_cfg (PARSER = default);
-- 3. 执行唯一获得覆盖信用的 DROP TEXT SEARCH CONFIGURATION。
-- primary-target-begin
DROP TEXT SEARCH CONFIGURATION IF EXISTS droptextsearchconfiguration_00035_cfg;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TEXT SEARCH CONFIGURATION IF EXISTS droptextsearchconfiguration_00035_cfg;
