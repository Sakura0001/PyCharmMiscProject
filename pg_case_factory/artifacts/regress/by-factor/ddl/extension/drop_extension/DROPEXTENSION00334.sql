-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP EXTENSION privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPEXTENSION00334
-- source_md: skills/pg-sql-generation/references/statements/ddl/extension/drop_extension.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/extension/drop_extension.yaml
-- primary_obligation_id: DROPEXTENSION-EXT|00334|drop_extension|pg_extension_catalog_query|drop_dependent_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP EXTENSION IF EXISTS dropextension_00334_ext CASCADE;
DROP OWNED BY dropextension_00334_actor;
DROP ROLE IF EXISTS dropextension_00334_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地扩展和因子专用夹具。
CREATE ROLE dropextension_00334_actor LOGIN NOSUPERUSER;
SELECT 1 AS target_extension_intentionally_absent;
SET ROLE dropextension_00334_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP EXTENSION。
-- primary-target-begin
DROP EXTENSION IF EXISTS dropextension_00334_ext;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS extension_absent FROM pg_catalog.pg_extension WHERE extname = 'dropextension_00334_ext' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP EXTENSION IF EXISTS dropextension_00334_ext CASCADE;
DROP OWNED BY dropextension_00334_actor;
DROP ROLE IF EXISTS dropextension_00334_actor;
