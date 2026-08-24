-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP ROUTINE dependent_object_conflict=cascade_with_dependent_succeeds
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPROUTINE00020
-- source_md: skills/pg-sql-generation/references/statements/ddl/routine/drop_routine.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/routine/drop_routine.yaml
-- primary_obligation_id: DROPROUTINE-SFV|sfv-324f13ce73fc37baddbc5bd7|drop_routine
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS droproutine_00020_dep CASCADE;
DROP ROUTINE IF EXISTS droproutine_00020_r CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地 routine 和因子专用夹具。
CREATE FUNCTION droproutine_00020_r RETURNS integer AS $$ BEGIN RETURN 1; END; $$ LANGUAGE plpgsql;
CREATE FUNCTION droproutine_00020_dep() RETURNS integer AS $$ BEGIN RETURN droproutine_00020_r(); END; $$ LANGUAGE plpgsql;
-- 3. 执行唯一获得覆盖信用的 DROP ROUTINE。
-- primary-target-begin
DROP ROUTINE droproutine_00020_r;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS routine_absent FROM pg_catalog.pg_proc WHERE proname = 'droproutine_00020_r' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP FUNCTION IF EXISTS droproutine_00020_dep CASCADE;
DROP ROUTINE IF EXISTS droproutine_00020_r CASCADE;
