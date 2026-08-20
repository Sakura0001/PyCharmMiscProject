-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER PROCEDURE object_state=different_signature_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPROCEDURE04568
-- source_md: skills/pg-sql-generation/references/statements/ddl/procedure/alter_procedure.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/procedure/alter_procedure.yaml
-- primary_obligation_id: AP-EXT|04568|rename|pg_proc_catalog_query|DROP_PROCEDURE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42883
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PROCEDURE IF EXISTS "alterprocedure_04568_select"(integer) CASCADE;
DROP PROCEDURE IF EXISTS "alterprocedure_04568_Mixed Name"(integer) CASCADE;
DROP ROLE IF EXISTS alterprocedure_04568_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE ROLE alterprocedure_04568_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterprocedure_04568_owner;
SET ROLE alterprocedure_04568_owner;
CREATE PROCEDURE "alterprocedure_04568_select"(integer) LANGUAGE sql AS $$ SELECT 1 $$;
RESET ROLE;
SET ROLE alterprocedure_04568_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER PROCEDURE。
-- primary-target-begin
ALTER PROCEDURE "alterprocedure_04568_select"(integer, text) RENAME TO "alterprocedure_04568_Mixed Name";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42883' AS target_sqlstate_matches_expected;
SELECT p.prokind, p.prosecdef FROM pg_catalog.pg_proc AS p WHERE p.proname = 'alterprocedure_04568_select' ORDER BY p.proname, p.oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PROCEDURE "alterprocedure_04568_select"(integer);
DROP PROCEDURE IF EXISTS "alterprocedure_04568_select"(integer) CASCADE;
DROP PROCEDURE IF EXISTS "alterprocedure_04568_Mixed Name"(integer) CASCADE;
DROP OWNED BY alterprocedure_04568_owner;
DROP ROLE IF EXISTS alterprocedure_04568_owner;
