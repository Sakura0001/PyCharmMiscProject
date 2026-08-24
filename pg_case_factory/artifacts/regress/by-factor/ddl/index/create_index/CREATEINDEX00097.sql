-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE INDEX with_storage=btree_fillfactor
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEINDEX00097
-- source_md: skills/pg-sql-generation/references/statements/ddl/index/create_index.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/index/create_index.yaml
-- primary_obligation_id: CINX-SFV|sfv-dbb2be3825e8db88773f4579|single_column_btree
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createindex_00097_t CASCADE;
DROP INDEX IF EXISTS createindex_00097_i CASCADE;
DROP INDEX IF EXISTS createindex_00097_idx CASCADE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE createindex_00097_t (id integer, val text, id2 integer, jdoc json);
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE INDEX。
-- primary-target-begin
CREATE INDEX createindex_00097_i ON createindex_00097_t USING btree (id) WITH (fillfactor = 80);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS index_count FROM pg_catalog.pg_class c WHERE c.relname = 'createindex_00097_i' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP INDEX IF EXISTS createindex_00097_i CASCADE;
DROP INDEX IF EXISTS createindex_00097_idx CASCADE;
DROP TABLE IF EXISTS createindex_00097_t CASCADE;
