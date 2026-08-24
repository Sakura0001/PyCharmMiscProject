-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER ROUTINE executor_privilege=non_owner_with_grant_option
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERROUTINE01160
-- source_md: skills/pg-sql-generation/references/statements/ddl/routine/alter_routine.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/routine/alter_routine.yaml
-- primary_obligation_id: AR-EXT|01160|security_definer|pg_proc_catalog|reset_config_parameter
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS alterroutine_01160_routine(integer) CASCADE;
DROP ROLE IF EXISTS alterroutine_01160_alter;
DROP ROLE IF EXISTS alterroutine_01160_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE ROLE alterroutine_01160_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterroutine_01160_owner;
CREATE ROLE alterroutine_01160_alter LOGIN;
SET ROLE alterroutine_01160_owner;
CREATE FUNCTION alterroutine_01160_routine(integer) RETURNS integer AS $$ SELECT 1 $$ LANGUAGE sql;
GRANT EXECUTE ON FUNCTION alterroutine_01160_routine(integer) TO alterroutine_01160_alter;
RESET ROLE;
SET ROLE alterroutine_01160_alter;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER ROUTINE。
-- primary-target-begin
ALTER ROUTINE alterroutine_01160_routine SECURITY DEFINER RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT p.proname, p.prokind, p.proowner::regrole, p.proleakproof, p.prosecdef, p.proparallel FROM pg_catalog.pg_proc AS p WHERE p.proname = 'alterroutine_01160_routine' ORDER BY p.proname, p.oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION IF EXISTS alterroutine_01160_routine(integer) CASCADE;
DROP FUNCTION IF EXISTS alterroutine_01160_routine(integer) CASCADE;
DROP OWNED BY alterroutine_01160_alter;
DROP ROLE IF EXISTS alterroutine_01160_alter;
DROP OWNED BY alterroutine_01160_owner;
DROP ROLE IF EXISTS alterroutine_01160_owner;
