-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SELECT target_relation_state=wrong_object_type
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SELECT17016
-- source_md: skills/pg-sql-generation/references/statements/dml/query/select.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/query/select.yaml
-- primary_obligation_id: SELECT-EXT|17016|returned_rows|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42809
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS select_17016_tbl, select_17016_src, select_17016_ref CASCADE;
DROP SEQUENCE IF EXISTS select_17016_seq;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SEQUENCE select_17016_seq;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 SELECT。
-- primary-target-begin
SELECT 1 FROM "select_17016_seq" WHERE id IN (SELECT val FROM select_17016_src);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42809' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS effect_state FROM pg_catalog.pg_class WHERE relname = 'select_17016_seq' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP SEQUENCE IF EXISTS select_17016_seq;
DROP TABLE IF EXISTS select_17016_tbl, select_17016_src, select_17016_ref CASCADE;
