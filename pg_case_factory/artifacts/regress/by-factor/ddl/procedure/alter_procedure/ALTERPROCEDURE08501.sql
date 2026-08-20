-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER PROCEDURE new_name_shape=quoted
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPROCEDURE08501
-- source_md: skills/pg-sql-generation/references/statements/ddl/procedure/alter_procedure.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/procedure/alter_procedure.yaml
-- primary_obligation_id: AP-EXT|08501|rename|pg_proc_catalog_query|DROP_PROCEDURE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PROCEDURE IF EXISTS alterprocedure_08501_src_schema.alterprocedure_08501_proc(integer) CASCADE;
DROP PROCEDURE IF EXISTS alterprocedure_08501_src_schema."alterprocedure_08501_Mixed Name"(integer) CASCADE;
DROP ROLE IF EXISTS alterprocedure_08501_owner;
DROP SCHEMA IF EXISTS alterprocedure_08501_src_schema CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS alterprocedure_08501_src_schema;
CREATE ROLE alterprocedure_08501_owner LOGIN;
GRANT CREATE ON SCHEMA public TO alterprocedure_08501_owner;
GRANT CREATE ON SCHEMA alterprocedure_08501_src_schema TO alterprocedure_08501_owner;
GRANT USAGE ON SCHEMA alterprocedure_08501_src_schema TO alterprocedure_08501_owner;
SET ROLE alterprocedure_08501_owner;
CREATE PROCEDURE alterprocedure_08501_src_schema.alterprocedure_08501_proc(integer) LANGUAGE sql AS $$ SELECT 1 $$;
RESET ROLE;
SET ROLE alterprocedure_08501_owner;
-- 3. 执行唯一获得覆盖信用的 ALTER PROCEDURE。
-- primary-target-begin
ALTER PROCEDURE alterprocedure_08501_src_schema.alterprocedure_08501_proc(integer) RENAME TO "alterprocedure_08501_Mixed Name";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT p.prokind, p.prosecdef FROM pg_catalog.pg_proc AS p WHERE p.proname = 'alterprocedure_08501_Mixed Name' ORDER BY p.proname, p.oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PROCEDURE alterprocedure_08501_src_schema."alterprocedure_08501_Mixed Name"(integer);
DROP PROCEDURE IF EXISTS alterprocedure_08501_src_schema.alterprocedure_08501_proc(integer) CASCADE;
DROP PROCEDURE IF EXISTS alterprocedure_08501_src_schema."alterprocedure_08501_Mixed Name"(integer) CASCADE;
DROP OWNED BY alterprocedure_08501_owner;
DROP ROLE IF EXISTS alterprocedure_08501_owner;
DROP SCHEMA IF EXISTS alterprocedure_08501_src_schema CASCADE;
