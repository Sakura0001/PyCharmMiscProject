-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP EXTENSION object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPEXTENSION00211
-- source_md: skills/pg-sql-generation/references/statements/ddl/extension/drop_extension.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/extension/drop_extension.yaml
-- primary_obligation_id: DROPEXTENSION-EXT|00211|drop_extension|error_assertion|drop_dependent_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP EXTENSION IF EXISTS dropextension_00211_ext CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地扩展和因子专用夹具。
CREATE EXTENSION dropextension_00211_ext;
-- 3. 执行唯一获得覆盖信用的 DROP EXTENSION。
-- primary-target-begin
DROP EXTENSION IF EXISTS dropextension_00211_ext CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS extension_absent FROM pg_catalog.pg_extension WHERE extname = 'dropextension_00211_ext' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP EXTENSION IF EXISTS dropextension_00211_ext CASCADE;
