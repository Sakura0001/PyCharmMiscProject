-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP INDEX dependency_type=unique_pk_constraint
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPINDEX00382
-- source_md: skills/pg-sql-generation/references/statements/ddl/index/drop_index.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/index/drop_index.yaml
-- primary_obligation_id: DROPINDEX-EXT|00382|drop_index|catalog_absence_check|cascade_auto_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropindex_00382_t CASCADE;
DROP INDEX IF EXISTS dropindex_00382_idx;
\set ON_ERROR_STOP on
-- 2. 创建完整本地索引和因子专用夹具。
CREATE TABLE dropindex_00382_t (c integer);
CREATE UNIQUE INDEX dropindex_00382_idx ON dropindex_00382_t USING btree (c);
ALTER TABLE dropindex_00382_t ADD CONSTRAINT dropindex_00382_ukey UNIQUE USING INDEX dropindex_00382_idx;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP INDEX。
-- primary-target-begin
DROP INDEX IF EXISTS dropindex_00382_idx RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS index_present FROM pg_catalog.pg_class WHERE relname = 'dropindex_00382_idx' AND relkind = 'i' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP INDEX IF EXISTS dropindex_00382_idx;
DROP TABLE IF EXISTS dropindex_00382_t CASCADE;
