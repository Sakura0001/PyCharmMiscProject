-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP ROUTINE dependent_objects=has_dependent_trigger
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPROUTINE00023
-- source_md: skills/pg-sql-generation/references/statements/ddl/routine/drop_routine.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/routine/drop_routine.yaml
-- primary_obligation_id: DROPROUTINE-SFV|sfv-41a4274aa210613a44b54b18|drop_routine
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droproutine_00023_t CASCADE;
DROP TRIGGER IF EXISTS droproutine_00023_trig ON droproutine_00023_t;
DROP ROUTINE IF EXISTS droproutine_00023_r CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地 routine 和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE FUNCTION droproutine_00023_r() RETURNS trigger AS $$ BEGIN RETURN NULL; END; $$ LANGUAGE plpgsql;
CREATE TABLE droproutine_00023_t (c integer);
CREATE TRIGGER droproutine_00023_trig BEFORE INSERT ON droproutine_00023_t FOR EACH ROW EXECUTE FUNCTION droproutine_00023_r();
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP ROUTINE。
-- primary-target-begin
DROP ROUTINE droproutine_00023_r;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS routine_present FROM pg_catalog.pg_proc WHERE proname = 'droproutine_00023_r' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TRIGGER IF EXISTS droproutine_00023_trig ON droproutine_00023_t;
DROP ROUTINE IF EXISTS droproutine_00023_r CASCADE;
DROP TABLE IF EXISTS droproutine_00023_t CASCADE;
