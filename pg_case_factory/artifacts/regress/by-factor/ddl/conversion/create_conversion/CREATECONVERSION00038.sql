-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE CONVERSION function_signature_mismatch=valid_conv_proc_signature
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATECONVERSION00038
-- source_md: skills/pg-sql-generation/references/statements/ddl/conversion/create_conversion.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/conversion/create_conversion.yaml
-- primary_obligation_id: CCONV-SFV|sfv-d2bab7a1e8abce650e020a38|create_conversion
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CONVERSION IF EXISTS createconversion_00038_conv CASCADE;
DROP FUNCTION IF EXISTS createconversion_00038_func CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createconversion_00038_func (integer, integer, cstring, internal, integer, boolean) RETURNS integer LANGUAGE internal AS 'ascii_to_mic';
-- 3. 执行唯一获得覆盖信用的 CREATE CONVERSION。
-- primary-target-begin
CREATE CONVERSION createconversion_00038_conv FOR 'UTF8' TO 'LATIN1' FROM createconversion_00038_func;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS conversion_state FROM pg_catalog.pg_conversion WHERE conname = 'createconversion_00038_conv' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP CONVERSION IF EXISTS createconversion_00038_conv CASCADE;
DROP FUNCTION IF EXISTS createconversion_00038_func CASCADE;
