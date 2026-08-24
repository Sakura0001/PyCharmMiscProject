-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP TRIGGER privilege_level=non_owner_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTRIGGER00328
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/drop_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/drop_trigger.yaml
-- primary_obligation_id: DROPTRIGGER-EXT|00328|drop_trigger|information_schema_triggers|DROP_TRIGGER_cascade
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droptrigger_00328_t CASCADE;
DROP FUNCTION IF EXISTS droptrigger_00328_fn() CASCADE;
DROP VIEW IF EXISTS droptrigger_00328_depv CASCADE;
DROP OWNED BY droptrigger_00328_actor;
DROP ROLE IF EXISTS droptrigger_00328_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地触发器和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE ROLE droptrigger_00328_actor LOGIN NOSUPERUSER;
CREATE TABLE droptrigger_00328_t (c integer);
CREATE FUNCTION droptrigger_00328_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NULL; END; $$;
CREATE TRIGGER "droptrigger_00328_qtrg" BEFORE INSERT ON droptrigger_00328_t FOR EACH ROW EXECUTE FUNCTION droptrigger_00328_fn();
CREATE VIEW droptrigger_00328_depv AS SELECT * FROM droptrigger_00328_t;
SET ROLE droptrigger_00328_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TRIGGER。
-- primary-target-begin
DROP TRIGGER IF EXISTS "droptrigger_00328_qtrg" ON public.droptrigger_00328_t CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS trigger_present FROM pg_catalog.pg_trigger WHERE tgname = 'droptrigger_00328_qtrg' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TRIGGER IF EXISTS "droptrigger_00328_qtrg" ON droptrigger_00328_t;
DROP FUNCTION IF EXISTS droptrigger_00328_fn() CASCADE;
DROP VIEW IF EXISTS droptrigger_00328_depv CASCADE;
DROP OWNED BY droptrigger_00328_actor;
DROP ROLE IF EXISTS droptrigger_00328_actor;
DROP TABLE IF EXISTS droptrigger_00328_t CASCADE;
