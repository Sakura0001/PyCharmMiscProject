-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP EXTENSION nonexistent_extension=extension_missing_no_if_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPEXTENSION00101
-- source_md: skills/pg-sql-generation/references/statements/ddl/extension/drop_extension.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/extension/drop_extension.yaml
-- primary_obligation_id: DROPEXTENSION-EXT|00101|drop_extension|pg_extension_catalog_query|recreate_extension
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP EXTENSION IF EXISTS dropextension_00101_ext CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地扩展和因子专用夹具。
SELECT 1 AS target_extension_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP EXTENSION。
-- primary-target-begin
DROP EXTENSION dropextension_00101_ext CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS extension_absent FROM pg_catalog.pg_extension WHERE extname = 'dropextension_00101_ext' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP EXTENSION IF EXISTS dropextension_00101_ext CASCADE;
