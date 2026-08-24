-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP SEQUENCE dependency_state=used_by_default_expression
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPSEQUENCE03926
-- source_md: skills/pg-sql-generation/references/statements/ddl/sequence/drop_sequence.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/sequence/drop_sequence.yaml
-- primary_obligation_id: DROPSEQUENCE-EXT|03926|drop_sequence|error_assertion|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropsequence_03926_t CASCADE;
DROP SEQUENCE IF EXISTS dropsequence_03926_seq CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地序列和因子专用夹具。
CREATE UNLOGGED SEQUENCE dropsequence_03926_seq;
CREATE TABLE dropsequence_03926_t (c integer DEFAULT nextval('dropsequence_03926_seq'));
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP SEQUENCE。
-- primary-target-begin
DROP SEQUENCE IF EXISTS dropsequence_03926_seq RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS sequence_present FROM pg_catalog.pg_class WHERE relname = 'dropsequence_03926_seq' AND relkind = 'S' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP SEQUENCE IF EXISTS dropsequence_03926_seq CASCADE;
DROP TABLE IF EXISTS dropsequence_03926_t CASCADE;
