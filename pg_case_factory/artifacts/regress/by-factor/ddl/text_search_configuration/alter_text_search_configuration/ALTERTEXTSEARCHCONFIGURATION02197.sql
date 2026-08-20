-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TEXT SEARCH CONFIGURATION object_state=not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTEXTSEARCHCONFIGURATION02197
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_configuration/alter_text_search_configuration.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_configuration/alter_text_search_configuration.yaml
-- primary_obligation_id: ATSC-EXT|02197|mapping_query|revert_owner
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH DICTIONARY IF EXISTS alter_text_search_configuration_02197_dict;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS target_config_intentionally_absent;
CREATE TEXT SEARCH DICTIONARY alter_text_search_configuration_02197_dict (template = simple);
ALTER TEXT SEARCH CONFIGURATION alter_text_search_configuration_02197_nosuchcfg ADD MAPPING FOR word WITH alter_text_search_configuration_02197_dict;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信度的 ALTER TEXT SEARCH CONFIGURATION。
-- primary-target-begin
ALTER TEXT SEARCH CONFIGURATION alter_text_search_configuration_02197_nosuchcfg DROP MAPPING IF EXISTS FOR word;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS mapping_state FROM pg_catalog.pg_ts_config_map WHERE mapcfg = (SELECT oid FROM pg_catalog.pg_ts_config WHERE cfgname = 'alter_text_search_configuration_02197_nosuchcfg') ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TEXT SEARCH DICTIONARY IF EXISTS alter_text_search_configuration_02197_dict;
