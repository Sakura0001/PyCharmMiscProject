-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP ROUTINE privilege_context=non_owner_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPROUTINE00206
-- source_md: skills/pg-sql-generation/references/statements/ddl/routine/drop_routine.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/routine/drop_routine.yaml
-- primary_obligation_id: DROPROUTINE-EXT|00206|drop_routine|pg_proc_catalog|drop_procedure
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS droproutine_00206_dep CASCADE;
DROP ROUTINE IF EXISTS droproutine_00206_r CASCADE;
DROP OWNED BY droproutine_00206_actor;
DROP ROLE IF EXISTS droproutine_00206_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地 routine 和因子专用夹具。
CREATE ROLE droproutine_00206_actor LOGIN NOSUPERUSER;
CREATE PROCEDURE droproutine_00206_r AS $$ BEGIN NULL; END; $$ LANGUAGE plpgsql;
CREATE FUNCTION droproutine_00206_dep() RETURNS integer AS $$ BEGIN CALL droproutine_00206_r(); RETURN 1; END; $$ LANGUAGE plpgsql;
SET ROLE droproutine_00206_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP ROUTINE。
-- primary-target-begin
DROP ROUTINE droproutine_00206_r CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS routine_present FROM pg_catalog.pg_proc WHERE proname = 'droproutine_00206_r' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION IF EXISTS droproutine_00206_dep CASCADE;
DROP ROUTINE IF EXISTS droproutine_00206_r CASCADE;
DROP OWNED BY droproutine_00206_actor;
DROP ROLE IF EXISTS droproutine_00206_actor;
