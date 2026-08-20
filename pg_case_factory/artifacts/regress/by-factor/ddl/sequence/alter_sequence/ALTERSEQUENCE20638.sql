-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SEQUENCE object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSEQUENCE20638
-- source_md: skills/pg-sql-generation/references/statements/ddl/sequence/alter_sequence.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/sequence/alter_sequence.yaml
-- primary_obligation_id: ALTSEQ-EXT|20638|alter_parameters|pg_class_catalog_query|DROP_SEQUENCE_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altersequence_20638_owned_tbl CASCADE;
DROP SEQUENCE IF EXISTS "altersequence_20638_user" CASCADE;
DROP ROLE IF EXISTS altersequence_20638_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地序列和因子专用夹具。
CREATE ROLE altersequence_20638_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altersequence_20638_owner;
CREATE SEQUENCE "altersequence_20638_user" AS bigint START WITH 1;
CREATE TABLE altersequence_20638_owned_tbl (col integer);
ALTER SEQUENCE "altersequence_20638_user" OWNER TO altersequence_20638_owner;
ALTER TABLE altersequence_20638_owned_tbl OWNER TO altersequence_20638_owner;
SET ROLE altersequence_20638_owner;
-- 3. 执行唯一获得覆盖信用的 ALTER SEQUENCE。
-- primary-target-begin
ALTER SEQUENCE IF EXISTS "altersequence_20638_user" OWNED BY altersequence_20638_owned_tbl.col;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS seq_exists FROM pg_catalog.pg_class WHERE relname = 'altersequence_20638_user' AND relkind = 'S' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SEQUENCE IF EXISTS "altersequence_20638_user" CASCADE;
DROP OWNED BY altersequence_20638_owner;
DROP ROLE IF EXISTS altersequence_20638_owner;
DROP TABLE IF EXISTS altersequence_20638_owned_tbl CASCADE;
