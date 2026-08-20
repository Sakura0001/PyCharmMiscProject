-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP FUNCTION privilege_level=non_owner_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPFUNCTION00519
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/drop_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/drop_function.yaml
-- primary_obligation_id: DROPFUNCTION-EXT|00519|drop_function|pg_proc_catalog_query|no_cleanup_needed
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OWNED BY dropfunction_00519_actor;
DROP ROLE IF EXISTS dropfunction_00519_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地函数和因子专用夹具。
CREATE ROLE dropfunction_00519_actor LOGIN NOSUPERUSER;
SELECT 1 AS target_function_intentionally_absent;
SET ROLE dropfunction_00519_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP FUNCTION。
-- primary-target-begin
DROP FUNCTION IF EXISTS dropfunction_00519_fn CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS function_absent FROM pg_catalog.pg_proc WHERE proname = 'dropfunction_00519_fn' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY dropfunction_00519_actor;
DROP ROLE IF EXISTS dropfunction_00519_actor;
