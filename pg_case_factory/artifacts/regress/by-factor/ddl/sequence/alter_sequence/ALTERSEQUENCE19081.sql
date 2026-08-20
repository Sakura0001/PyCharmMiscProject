-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SEQUENCE owned_by_table_dependency=different_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSEQUENCE19081
-- source_md: skills/pg-sql-generation/references/statements/ddl/sequence/alter_sequence.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/sequence/alter_sequence.yaml
-- primary_obligation_id: ALTSEQ-EXT|19081|alter_parameters|sequence_inspection_query|DROP_SEQUENCE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altersequence_19081_owned_tbl CASCADE;
DROP SEQUENCE IF EXISTS altersequence_19081_seq CASCADE;
DROP ROLE IF EXISTS altersequence_19081_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地序列和因子专用夹具。
CREATE ROLE altersequence_19081_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altersequence_19081_owner;
CREATE SEQUENCE altersequence_19081_seq AS bigint START WITH 1;
CREATE TABLE altersequence_19081_owned_tbl (col integer);
ALTER SEQUENCE altersequence_19081_seq OWNER TO altersequence_19081_owner;
ALTER TABLE altersequence_19081_owned_tbl OWNER TO altersequence_19081_owner;
SET ROLE altersequence_19081_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SEQUENCE。
-- primary-target-begin
ALTER SEQUENCE altersequence_19081_seq OWNED BY altersequence_19081_owned_tbl.col;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT s.seqtypid::regtype AS seqtype, s.seqstart, s.seqincrement, s.seqmin, s.seqmax, s.seqcache, s.seqcycle FROM pg_catalog.pg_sequence AS s JOIN pg_catalog.pg_class AS c ON s.seqrelid = c.oid WHERE c.relname = 'altersequence_19081_seq' AND c.relkind = 'S' ORDER BY s.seqtypid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SEQUENCE IF EXISTS altersequence_19081_seq CASCADE;
DROP OWNED BY altersequence_19081_owner;
DROP ROLE IF EXISTS altersequence_19081_owner;
DROP TABLE IF EXISTS altersequence_19081_owned_tbl CASCADE;
