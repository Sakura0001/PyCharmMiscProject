-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP TRIGGER object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTRIGGER04107
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/drop_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/drop_trigger.yaml
-- primary_obligation_id: DROPTRIGGER-EXT|04107|drop_trigger|pg_trigger_catalog_query|no_cleanup_needed
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droptrigger_04107_t CASCADE;
DROP FUNCTION IF EXISTS droptrigger_04107_fn() CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地触发器和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE TABLE droptrigger_04107_t (c integer);
CREATE FUNCTION droptrigger_04107_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NULL; END; $$;
CREATE TRIGGER "droptrigger_04107_qtrg" BEFORE INSERT ON droptrigger_04107_t FOR EACH ROW EXECUTE FUNCTION droptrigger_04107_fn();
-- 3. 执行唯一获得覆盖信用的 DROP TRIGGER。
-- primary-target-begin
DROP TRIGGER "droptrigger_04107_qtrg" ON public.droptrigger_04107_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS trigger_absent FROM pg_catalog.pg_trigger WHERE tgname = 'droptrigger_04107_qtrg' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TRIGGER IF EXISTS "droptrigger_04107_qtrg" ON droptrigger_04107_t;
DROP FUNCTION IF EXISTS droptrigger_04107_fn() CASCADE;
DROP TABLE IF EXISTS droptrigger_04107_t CASCADE;
