-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER INDEX permission_boundary=insufficient_tablespace_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERINDEX00041
-- source_md: skills/pg-sql-generation/references/statements/ddl/index/alter_index.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/index/alter_index.yaml
-- primary_obligation_id: AI-SFV|sfv-56cc1958e6619baa37f9c3fa|all_in_tablespace
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterindex_00041_t CASCADE;
DROP INDEX IF EXISTS alterindex_00041_idx CASCADE;
DROP TABLESPACE IF EXISTS alterindex_00041_dst_tbs;
DROP TABLESPACE IF EXISTS alterindex_00041_move_tbs;
DROP ROLE IF EXISTS alterindex_00041_nopriv;
\set ON_ERROR_STOP on
-- 2. 创建完整本地索引和因子专用夹具。
CREATE TABLESPACE alterindex_00041_dst_tbs LOCATION '/tmp/alterindex_00041_dst_tbs';
CREATE TABLESPACE alterindex_00041_move_tbs LOCATION '/tmp/alterindex_00041_move_tbs';
CREATE TABLE alterindex_00041_t (id integer, tsv tsvector, pt point, rng int4range);
CREATE INDEX alterindex_00041_idx ON alterindex_00041_t USING btree (id) TABLESPACE alterindex_00041_dst_tbs;
CREATE ROLE alterindex_00041_nopriv;
SET ROLE alterindex_00041_nopriv;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER INDEX。
-- primary-target-begin
ALTER INDEX ALL IN TABLESPACE alterindex_00041_dst_tbs SET TABLESPACE alterindex_00041_move_tbs;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS target_index_visible FROM pg_catalog.pg_class AS c WHERE c.relname = 'alterindex_00041_idx' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP INDEX IF EXISTS alterindex_00041_idx CASCADE;
DROP TABLESPACE IF EXISTS alterindex_00041_dst_tbs;
DROP TABLESPACE IF EXISTS alterindex_00041_move_tbs;
DROP ROLE IF EXISTS alterindex_00041_nopriv;
DROP TABLE IF EXISTS alterindex_00041_t CASCADE;
