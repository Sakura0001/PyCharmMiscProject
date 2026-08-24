-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP CONVERSION privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPCONVERSION00159
-- source_md: skills/pg-sql-generation/references/statements/ddl/conversion/drop_conversion.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/conversion/drop_conversion.yaml
-- primary_obligation_id: DROPCONVERSION-EXT|00159|drop_conversion|catalog_query_pg_conversion|drop_conversion
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CONVERSION IF EXISTS "dropconversion_00159_QuotedConv";
DROP ROLE IF EXISTS dropconversion_00159_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地转换和因子专用夹具。
CREATE ROLE dropconversion_00159_actor LOGIN NOSUPERUSER;
CREATE CONVERSION "dropconversion_00159_QuotedConv" FOR 'LATIN1' TO 'UTF8' FROM dropconversion_00159_convfn;
SET ROLE dropconversion_00159_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP CONVERSION。
-- primary-target-begin
DROP CONVERSION "dropconversion_00159_QuotedConv";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS conversion_present FROM pg_catalog.pg_conversion WHERE conname = 'dropconversion_00159_QuotedConv' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP CONVERSION IF EXISTS "dropconversion_00159_QuotedConv";
DROP OWNED BY dropconversion_00159_actor;
DROP ROLE IF EXISTS dropconversion_00159_actor;
