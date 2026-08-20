-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TEXT SEARCH CONFIGURATION alter_action=alter_mapping_replace
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTEXTSEARCHCONFIGURATION00012
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_configuration/alter_text_search_configuration.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_configuration/alter_text_search_configuration.yaml
-- primary_obligation_id: ATSC-SFV|sfv-07bef02cfe62c8f694987d46|alter_mapping_replace
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH CONFIGURATION IF EXISTS alter_text_search_configuration_00012_cfg;
DROP TEXT SEARCH DICTIONARY IF EXISTS alter_text_search_configuration_00012_dict;
DROP TEXT SEARCH DICTIONARY IF EXISTS alter_text_search_configuration_00012_olddict;
DROP TEXT SEARCH DICTIONARY IF EXISTS alter_text_search_configuration_00012_newdict;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TEXT SEARCH CONFIGURATION alter_text_search_configuration_00012_cfg (parser = default);
CREATE TEXT SEARCH DICTIONARY alter_text_search_configuration_00012_dict (template = simple);
CREATE TEXT SEARCH DICTIONARY alter_text_search_configuration_00012_olddict (template = simple);
CREATE TEXT SEARCH DICTIONARY alter_text_search_configuration_00012_newdict (template = simple);
ALTER TEXT SEARCH CONFIGURATION alter_text_search_configuration_00012_cfg ADD MAPPING FOR word WITH alter_text_search_configuration_00012_olddict;
-- 3. 执行唯一获得覆盖信度的 ALTER TEXT SEARCH CONFIGURATION。
-- primary-target-begin
ALTER TEXT SEARCH CONFIGURATION alter_text_search_configuration_00012_cfg ALTER MAPPING REPLACE alter_text_search_configuration_00012_olddict WITH alter_text_search_configuration_00012_newdict;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS config_state FROM pg_catalog.pg_ts_config WHERE cfgname = 'alter_text_search_configuration_00012_cfg' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TEXT SEARCH CONFIGURATION IF EXISTS alter_text_search_configuration_00012_cfg;
DROP TEXT SEARCH DICTIONARY IF EXISTS alter_text_search_configuration_00012_dict;
DROP TEXT SEARCH DICTIONARY IF EXISTS alter_text_search_configuration_00012_olddict;
DROP TEXT SEARCH DICTIONARY IF EXISTS alter_text_search_configuration_00012_newdict;
