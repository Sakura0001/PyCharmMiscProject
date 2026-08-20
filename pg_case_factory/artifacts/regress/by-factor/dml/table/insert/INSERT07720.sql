-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : INSERT target_relation_state=wrong_object_type
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: INSERT07720
-- source_md: skills/pg-sql-generation/references/statements/dml/table/insert.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/insert.yaml
-- primary_obligation_id: INSERT-EXT|07720|catalog_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42809
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS insert_07720_tbl, insert_07720_src, insert_07720_ref CASCADE;
DROP SEQUENCE IF EXISTS insert_07720_seq;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SEQUENCE insert_07720_seq;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 INSERT。
-- primary-target-begin
WITH insert_07720_cte AS (SELECT 1 AS val)
INSERT INTO insert_07720_seq (id, val) SELECT 1, 100 WHERE false;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42809' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS relation_state FROM pg_catalog.pg_class WHERE relname = 'insert_07720_seq' AND relkind = 'r' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP SEQUENCE IF EXISTS insert_07720_seq;
DROP TABLE IF EXISTS insert_07720_tbl, insert_07720_src, insert_07720_ref CASCADE;
