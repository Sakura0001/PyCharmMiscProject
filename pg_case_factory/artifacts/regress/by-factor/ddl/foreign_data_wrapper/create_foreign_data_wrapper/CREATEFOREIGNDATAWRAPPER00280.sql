-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE FOREIGN DATA WRAPPER privilege_level=non_superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEFOREIGNDATAWRAPPER00280
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_data_wrapper/create_foreign_data_wrapper.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_data_wrapper/create_foreign_data_wrapper.yaml
-- primary_obligation_id: CFDW-EXT|00280|error_assertion|drop_handler_function
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FOREIGN DATA WRAPPER IF EXISTS "createforeigndatawrapper_00280_Mixed Fdw" CASCADE;
DROP OWNED BY createforeigndatawrapper_00280_actor CASCADE;
DROP ROLE IF EXISTS createforeigndatawrapper_00280_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createforeigndatawrapper_00280_actor LOGIN NOSUPERUSER;
SET ROLE createforeigndatawrapper_00280_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE FOREIGN DATA WRAPPER。
-- primary-target-begin
CREATE FOREIGN DATA WRAPPER "createforeigndatawrapper_00280_Mixed Fdw" NO HANDLER NO VALIDATOR OPTIONS ('createforeigndatawrapper_00280_opt1' 'val1', 'createforeigndatawrapper_00280_opt2' 'val2');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FOREIGN DATA WRAPPER IF EXISTS "createforeigndatawrapper_00280_Mixed Fdw" CASCADE;
DROP OWNED BY createforeigndatawrapper_00280_actor CASCADE;
DROP ROLE IF EXISTS createforeigndatawrapper_00280_actor;
