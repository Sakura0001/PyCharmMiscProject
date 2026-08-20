-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER PROCEDURE new_name_shape=reserved_word
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPROCEDURE08833
-- source_md: skills/pg-sql-generation/references/statements/ddl/procedure/alter_procedure.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/procedure/alter_procedure.yaml
-- primary_obligation_id: AP-EXT|08833|rename|pg_get_functiondef|DROP_PROCEDURE_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PROCEDURE IF EXISTS alterprocedure_08833_src_schema.alterprocedure_08833_proc(integer) CASCADE;
DROP PROCEDURE IF EXISTS alterprocedure_08833_src_schema."alterprocedure_08833_from"(integer) CASCADE;
DROP SCHEMA IF EXISTS alterprocedure_08833_src_schema CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS alterprocedure_08833_src_schema;
CREATE PROCEDURE alterprocedure_08833_src_schema.alterprocedure_08833_proc(integer) LANGUAGE sql AS $$ SELECT 1 $$;
-- 3. 执行唯一获得覆盖信用的 ALTER PROCEDURE。
-- primary-target-begin
ALTER PROCEDURE alterprocedure_08833_src_schema.alterprocedure_08833_proc(integer) RENAME TO "alterprocedure_08833_from";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT pg_get_functiondef(p.oid) FROM pg_catalog.pg_proc AS p WHERE p.proname = 'alterprocedure_08833_from' ORDER BY p.oid;
-- 5. 清理全部本编号对象。
DROP PROCEDURE alterprocedure_08833_src_schema."alterprocedure_08833_from"(integer) CASCADE;
DROP PROCEDURE IF EXISTS alterprocedure_08833_src_schema.alterprocedure_08833_proc(integer) CASCADE;
DROP PROCEDURE IF EXISTS alterprocedure_08833_src_schema."alterprocedure_08833_from"(integer) CASCADE;
DROP SCHEMA IF EXISTS alterprocedure_08833_src_schema CASCADE;
