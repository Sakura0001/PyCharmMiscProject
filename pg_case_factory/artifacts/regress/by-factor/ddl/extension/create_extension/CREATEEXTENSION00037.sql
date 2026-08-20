-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE EXTENSION nonexistent_extension_script=script_missing
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEEXTENSION00037
-- source_md: skills/pg-sql-generation/references/statements/ddl/extension/create_extension.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/extension/create_extension.yaml
-- primary_obligation_id: CE-SFV|sfv-12eae5b0e8ce7be4ea676c5e|create_extension
-- expected_outcome: expected_failure
-- expected_sqlstate: 58P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP EXTENSION IF EXISTS createextension_00037_nonexistent_ext CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE EXTENSION。
-- primary-target-begin
CREATE EXTENSION createextension_00037_nonexistent_ext;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '58P01' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS ext_state FROM pg_catalog.pg_extension WHERE extname = 'createextension_00037_nonexistent_ext' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP EXTENSION IF EXISTS createextension_00037_nonexistent_ext CASCADE;
