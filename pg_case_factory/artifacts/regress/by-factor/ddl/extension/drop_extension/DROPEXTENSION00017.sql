-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP EXTENSION extension_name_shape=quoted_id
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPEXTENSION00017
-- source_md: skills/pg-sql-generation/references/statements/ddl/extension/drop_extension.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/extension/drop_extension.yaml
-- primary_obligation_id: DROPEXTENSION-SFV|sfv-95fd97e9a5e8d192215403e3|drop_extension
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP EXTENSION IF EXISTS "dropextension_00017_QuotedExt" CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地扩展和因子专用夹具。
CREATE EXTENSION "dropextension_00017_QuotedExt";
-- 3. 执行唯一获得覆盖信用的 DROP EXTENSION。
-- primary-target-begin
DROP EXTENSION "dropextension_00017_QuotedExt";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS extension_absent FROM pg_catalog.pg_extension WHERE extname = 'dropextension_00017_QuotedExt' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP EXTENSION IF EXISTS "dropextension_00017_QuotedExt" CASCADE;
