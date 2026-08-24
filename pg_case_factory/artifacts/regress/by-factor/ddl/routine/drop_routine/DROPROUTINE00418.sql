-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP ROUTINE routine_existence=routine_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPROUTINE00418
-- source_md: skills/pg-sql-generation/references/statements/ddl/routine/drop_routine.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/routine/drop_routine.yaml
-- primary_obligation_id: DROPROUTINE-EXT|00418|drop_routine|pg_proc_catalog|cascade_drop_with_dependents
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS droproutine_00418_dep CASCADE;
DROP ROUTINE IF EXISTS droproutine_00418_r CASCADE;
DROP OWNED BY droproutine_00418_actor;
DROP ROLE IF EXISTS droproutine_00418_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地 routine 和因子专用夹具。
CREATE ROLE droproutine_00418_actor LOGIN NOSUPERUSER;
SET ROLE droproutine_00418_actor;
CREATE PROCEDURE droproutine_00418_r AS $$ BEGIN NULL; END; $$ LANGUAGE plpgsql;
CREATE FUNCTION droproutine_00418_dep() RETURNS integer AS $$ BEGIN CALL droproutine_00418_r(); RETURN 1; END; $$ LANGUAGE plpgsql;
-- 3. 执行唯一获得覆盖信用的 DROP ROUTINE。
-- primary-target-begin
DROP ROUTINE IF EXISTS droproutine_00418_r CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS routine_absent FROM pg_catalog.pg_proc WHERE proname = 'droproutine_00418_r' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION IF EXISTS droproutine_00418_dep CASCADE;
DROP ROUTINE IF EXISTS droproutine_00418_r CASCADE;
DROP OWNED BY droproutine_00418_actor;
DROP ROLE IF EXISTS droproutine_00418_actor;
