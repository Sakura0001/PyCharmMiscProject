-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE INDEX concurrent_failure=in_transaction_block
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEINDEX00026
-- source_md: skills/pg-sql-generation/references/statements/ddl/index/create_index.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/index/create_index.yaml
-- primary_obligation_id: CINX-SFV|sfv-6e586884ae0603152f3f7bd8|single_column_btree
-- expected_outcome: expected_failure
-- expected_sqlstate: 0A000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createindex_00026_t CASCADE;
DROP INDEX IF EXISTS createindex_00026_i CASCADE;
DROP INDEX IF EXISTS createindex_00026_idx CASCADE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE createindex_00026_t (id integer, val text, id2 integer, jdoc json);
BEGIN;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE INDEX。
-- primary-target-begin
CREATE INDEX CONCURRENTLY createindex_00026_i ON createindex_00026_t USING btree (id);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
ROLLBACK;
SELECT :'target_sqlstate' = '0A000' AS target_sqlstate_matches_expected;
SELECT count(*) AS index_count FROM pg_catalog.pg_class c WHERE c.relname = 'createindex_00026_i' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP INDEX IF EXISTS createindex_00026_i CASCADE;
DROP INDEX IF EXISTS createindex_00026_idx CASCADE;
DROP TABLE IF EXISTS createindex_00026_t CASCADE;
