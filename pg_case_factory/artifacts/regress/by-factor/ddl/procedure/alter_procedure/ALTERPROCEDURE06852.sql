-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER PROCEDURE schema_target=pg_catalog_reserved
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPROCEDURE06852
-- source_md: skills/pg-sql-generation/references/statements/ddl/procedure/alter_procedure.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/procedure/alter_procedure.yaml
-- primary_obligation_id: AP-EXT|06852|set_schema|pg_get_functiondef|DROP_PROCEDURE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PROCEDURE IF EXISTS "alterprocedure_06852_Mixed Procedure"(integer) CASCADE;
DROP ROLE IF EXISTS alterprocedure_06852_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE ROLE alterprocedure_06852_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterprocedure_06852_owner;
SET ROLE alterprocedure_06852_owner;
CREATE PROCEDURE "alterprocedure_06852_Mixed Procedure"(integer) LANGUAGE sql AS $$ SELECT 1 $$;
RESET ROLE;
SET ROLE alterprocedure_06852_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER PROCEDURE。
-- primary-target-begin
ALTER PROCEDURE "alterprocedure_06852_Mixed Procedure"(integer) SET SCHEMA pg_catalog;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT pg_get_functiondef(p.oid) FROM pg_catalog.pg_proc AS p WHERE p.proname = 'alterprocedure_06852_Mixed Procedure' ORDER BY p.oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PROCEDURE IF EXISTS "alterprocedure_06852_Mixed Procedure"(integer);
DROP PROCEDURE IF EXISTS "alterprocedure_06852_Mixed Procedure"(integer) CASCADE;
DROP OWNED BY alterprocedure_06852_owner;
DROP ROLE IF EXISTS alterprocedure_06852_owner;
