-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP INDEX object_state=not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPINDEX00267
-- source_md: skills/pg-sql-generation/references/statements/ddl/index/drop_index.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/index/drop_index.yaml
-- primary_obligation_id: DROPINDEX-EXT|00267|drop_index|constraint_integrity_check|explicit_drop
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropindex_00267_t CASCADE;
DROP INDEX IF EXISTS dropindex_00267_idx;
\set ON_ERROR_STOP on
-- 2. 创建完整本地索引和因子专用夹具。
CREATE TABLE dropindex_00267_t (c integer);
SELECT 1 AS target_index_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP INDEX。
-- primary-target-begin
DROP INDEX dropindex_00267_idx RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS index_absent FROM pg_catalog.pg_class WHERE relname = 'dropindex_00267_idx' AND relkind = 'i' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP INDEX IF EXISTS dropindex_00267_idx;
DROP TABLE IF EXISTS dropindex_00267_t CASCADE;
