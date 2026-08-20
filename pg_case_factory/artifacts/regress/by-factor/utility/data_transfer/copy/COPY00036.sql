-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : COPY resource_boundary=missing_file_or_library
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: COPY00036
-- source_md: skills/pg-sql-generation/references/statements/utility/data_transfer/copy.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/data_transfer/copy.yaml
-- primary_obligation_id: COPY-SFV|sfv-d97f4f7f5a9754f2dd678c69|copy_from
-- expected_outcome: expected_failure
-- expected_sqlstate: 58P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS copy_00036_t;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE copy_00036_t (copy_00036_c int);
INSERT INTO copy_00036_t VALUES (1), (2), (3);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 COPY。
-- primary-target-begin
COPY copy_00036_t FROM 'copy_00036_no_such_file.csv';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '58P01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS rows_in_table FROM pg_catalog.pg_class WHERE relname = 'copy_00036_t' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS copy_00036_t;
