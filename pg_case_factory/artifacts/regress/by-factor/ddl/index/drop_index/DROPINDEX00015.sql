-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP INDEX if_exists=false
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPINDEX00015
-- source_md: skills/pg-sql-generation/references/statements/ddl/index/drop_index.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/index/drop_index.yaml
-- primary_obligation_id: DROPINDEX-SFV|sfv-b93253a8d4f8d1d12a11cce9|drop_index
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropindex_00015_t CASCADE;
DROP INDEX IF EXISTS dropindex_00015_idx;
\set ON_ERROR_STOP on
-- 2. 创建完整本地索引和因子专用夹具。
CREATE TABLE dropindex_00015_t (c integer);
CREATE INDEX dropindex_00015_idx ON dropindex_00015_t USING btree (c);
-- 3. 执行唯一获得覆盖信用的 DROP INDEX。
-- primary-target-begin
DROP INDEX dropindex_00015_idx RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS index_absent FROM pg_catalog.pg_class WHERE relname = 'dropindex_00015_idx' AND relkind = 'i' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP INDEX IF EXISTS dropindex_00015_idx;
DROP TABLE IF EXISTS dropindex_00015_t CASCADE;
