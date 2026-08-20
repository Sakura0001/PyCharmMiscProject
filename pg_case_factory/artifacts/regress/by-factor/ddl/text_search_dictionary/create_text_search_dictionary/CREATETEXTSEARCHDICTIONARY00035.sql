-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TEXT SEARCH DICTIONARY schema_permission_denied=lacks_create_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETEXTSEARCHDICTIONARY00035
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_dictionary/create_text_search_dictionary.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_dictionary/create_text_search_dictionary.yaml
-- primary_obligation_id: CTSD-SFV|sfv-8b3dac759aff3d26bb7876d2|create_dictionary
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TEXT SEARCH DICTIONARY IF EXISTS createtextsearchdictionary_00035_dict CASCADE;
DROP TEXT SEARCH TEMPLATE IF EXISTS createtextsearchdictionary_00035_tmpl;
RESET ROLE;
DROP OWNED BY createtextsearchdictionary_00035_actor CASCADE;
DROP ROLE IF EXISTS createtextsearchdictionary_00035_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createtextsearchdictionary_00035_actor LOGIN NOSUPERUSER;
SET ROLE createtextsearchdictionary_00035_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TEXT SEARCH DICTIONARY。
-- primary-target-begin
CREATE TEXT SEARCH DICTIONARY createtextsearchdictionary_00035_dict (TEMPLATE = simple);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS dict_state FROM pg_catalog.pg_ts_dict WHERE dictname = 'createtextsearchdictionary_00035_dict' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TEXT SEARCH DICTIONARY IF EXISTS createtextsearchdictionary_00035_dict CASCADE;
DROP OWNED BY createtextsearchdictionary_00035_actor CASCADE;
DROP ROLE IF EXISTS createtextsearchdictionary_00035_actor;
