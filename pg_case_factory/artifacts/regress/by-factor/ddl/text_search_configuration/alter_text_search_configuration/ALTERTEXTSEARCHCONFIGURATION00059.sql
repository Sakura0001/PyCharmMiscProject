-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TEXT SEARCH CONFIGURATION owner_name_shape=nonexistent_role
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTEXTSEARCHCONFIGURATION00059
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_configuration/alter_text_search_configuration.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_configuration/alter_text_search_configuration.yaml
-- primary_obligation_id: ATSC-SFV|sfv-bc21c472f8194c8d85b26d9d|owner
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH CONFIGURATION IF EXISTS alter_text_search_configuration_00059_cfg;
DROP OWNED BY alter_text_search_configuration_00059_newowner CASCADE;
DROP ROLE IF EXISTS alter_text_search_configuration_00059_newowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TEXT SEARCH CONFIGURATION alter_text_search_configuration_00059_cfg (parser = default);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信度的 ALTER TEXT SEARCH CONFIGURATION。
-- primary-target-begin
ALTER TEXT SEARCH CONFIGURATION alter_text_search_configuration_00059_cfg OWNER TO alter_text_search_configuration_00059_newowner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS config_state FROM pg_catalog.pg_ts_config WHERE cfgname = 'alter_text_search_configuration_00059_cfg' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TEXT SEARCH CONFIGURATION IF EXISTS alter_text_search_configuration_00059_cfg;
DROP OWNED BY alter_text_search_configuration_00059_newowner CASCADE;
DROP ROLE IF EXISTS alter_text_search_configuration_00059_newowner;
