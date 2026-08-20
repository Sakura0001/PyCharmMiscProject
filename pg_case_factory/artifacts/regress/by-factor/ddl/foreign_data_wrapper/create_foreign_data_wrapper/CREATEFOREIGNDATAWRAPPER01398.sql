-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE FOREIGN DATA WRAPPER target_action=create_foreign_data_wrapper
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEFOREIGNDATAWRAPPER01398
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_data_wrapper/create_foreign_data_wrapper.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_data_wrapper/create_foreign_data_wrapper.yaml
-- primary_obligation_id: CFDW-EXT|01398|pg_foreign_data_wrapper_catalog|role_cleanup
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FOREIGN DATA WRAPPER IF EXISTS "createforeigndatawrapper_01398_select" CASCADE;
DROP FUNCTION IF EXISTS createforeigndatawrapper_01398_validator(text[], oid);
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createforeigndatawrapper_01398_validator(text[], oid) RETURNS void AS 'MODULE_PATHNAME', 'cfdw_validator' LANGUAGE C STRICT;
-- 3. 执行唯一获得覆盖信用的 CREATE FOREIGN DATA WRAPPER。
-- primary-target-begin
CREATE FOREIGN DATA WRAPPER "createforeigndatawrapper_01398_select" NO HANDLER VALIDATOR createforeigndatawrapper_01398_validator;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS fdw_state FROM pg_catalog.pg_foreign_data_wrapper WHERE fdwname = 'createforeigndatawrapper_01398_select' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP FOREIGN DATA WRAPPER IF EXISTS "createforeigndatawrapper_01398_select" CASCADE;
DROP FUNCTION IF EXISTS createforeigndatawrapper_01398_validator(text[], oid);
