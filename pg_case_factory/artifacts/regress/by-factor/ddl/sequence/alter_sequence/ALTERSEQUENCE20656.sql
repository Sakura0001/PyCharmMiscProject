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
-- case_id: ALTERSEQUENCE20656
-- source_md: skills/pg-sql-generation/references/statements/ddl/sequence/alter_sequence.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/sequence/alter_sequence.yaml
-- primary_obligation_id: ALTSEQ-EXT|20656|alter_parameters|nextval_call|DROP_SEQUENCE_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altersequence_20656_owned_tbl CASCADE;
DROP SEQUENCE IF EXISTS altersequence_20656_sch.altersequence_20656_seq CASCADE;
DROP SCHEMA IF EXISTS altersequence_20656_sch CASCADE;
DROP ROLE IF EXISTS altersequence_20656_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地序列和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altersequence_20656_sch;
CREATE ROLE altersequence_20656_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altersequence_20656_owner;
CREATE SEQUENCE altersequence_20656_sch.altersequence_20656_seq AS bigint START WITH 1;
CREATE TABLE altersequence_20656_owned_tbl (col integer);
ALTER SEQUENCE altersequence_20656_sch.altersequence_20656_seq OWNER TO altersequence_20656_owner;
ALTER TABLE altersequence_20656_owned_tbl OWNER TO altersequence_20656_owner;
SET ROLE altersequence_20656_owner;
-- 3. 执行唯一获得覆盖信用的 ALTER SEQUENCE。
-- primary-target-begin
ALTER SEQUENCE IF EXISTS altersequence_20656_sch.altersequence_20656_seq OWNED BY altersequence_20656_owned_tbl.col;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT nextval('altersequence_20656_sch.altersequence_20656_seq') AS nextval_verified;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SEQUENCE IF EXISTS altersequence_20656_sch.altersequence_20656_seq CASCADE;
DROP SCHEMA IF EXISTS altersequence_20656_sch CASCADE;
DROP OWNED BY altersequence_20656_owner;
DROP ROLE IF EXISTS altersequence_20656_owner;
DROP TABLE IF EXISTS altersequence_20656_owned_tbl CASCADE;
