-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : COPY resource_boundary=locked_relation
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: COPY03100
-- source_md: skills/pg-sql-generation/references/statements/utility/data_transfer/copy.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/data_transfer/copy.yaml
-- primary_obligation_id: COPY-EXT|03100|catalog_query|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 55P03
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS copy_03100_t;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE copy_03100_t (copy_03100_c int);
INSERT INTO copy_03100_t VALUES (1), (2), (3);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 COPY。
-- primary-target-begin
COPY copy_03100_t TO 'copy_03100_out.csv';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '55P03' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS table_present FROM pg_catalog.pg_class WHERE relname = 'copy_03100_t' ORDER BY count(*);
-- 5. 清理全部本编号对象。
ROLLBACK;
DROP TABLE IF EXISTS copy_03100_t;
