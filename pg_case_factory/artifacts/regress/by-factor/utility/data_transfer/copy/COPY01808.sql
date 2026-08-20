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
-- case_id: COPY01808
-- source_md: skills/pg-sql-generation/references/statements/utility/data_transfer/copy.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/data_transfer/copy.yaml
-- primary_obligation_id: COPY-EXT|01808|effect_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 58P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS copy_01808_t;
DROP ROLE IF EXISTS copy_01808_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE copy_01808_actor LOGIN NOSUPERUSER;
CREATE TABLE copy_01808_t (copy_01808_c int);
INSERT INTO copy_01808_t VALUES (1), (2), (3);
GRANT SELECT, INSERT ON copy_01808_t TO copy_01808_actor;
SET ROLE copy_01808_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 COPY。
-- primary-target-begin
COPY "copy_01808_t" TO STDOUT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '58P01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS rows_in_table FROM pg_catalog.pg_class WHERE relname = 'copy_01808_t' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS copy_01808_actor;
DROP TABLE IF EXISTS copy_01808_t;
