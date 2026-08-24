-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP CONVERSION conversion_not_exist=conversion_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPCONVERSION00245
-- source_md: skills/pg-sql-generation/references/statements/ddl/conversion/drop_conversion.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/conversion/drop_conversion.yaml
-- primary_obligation_id: DROPCONVERSION-EXT|00245|drop_conversion|error_assertion|drop_conversion
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CONVERSION IF EXISTS "dropconversion_00245_QuotedConv";
\set ON_ERROR_STOP on
-- 2. 创建完整本地转换和因子专用夹具。
SELECT 1 AS target_conversion_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP CONVERSION。
-- primary-target-begin
DROP CONVERSION "dropconversion_00245_QuotedConv";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS conversion_absent FROM pg_catalog.pg_conversion WHERE conname = 'dropconversion_00245_QuotedConv' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP CONVERSION IF EXISTS "dropconversion_00245_QuotedConv";
