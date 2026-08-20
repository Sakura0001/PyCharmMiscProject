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
-- case_id: COPY01269
-- source_md: skills/pg-sql-generation/references/statements/utility/data_transfer/copy.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/data_transfer/copy.yaml
-- primary_obligation_id: COPY-EXT|01269|effect_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 58P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS copy_01269_t;
DROP ROLE IF EXISTS copy_01269_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE copy_01269_actor LOGIN NOSUPERUSER;
CREATE TABLE copy_01269_t (copy_01269_c int);
INSERT INTO copy_01269_t VALUES (1), (2), (3);
GRANT SELECT, INSERT ON copy_01269_t TO copy_01269_actor;
SET ROLE copy_01269_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 COPY。
-- primary-target-begin
COPY public.copy_01269_t (copy_01269_c) FROM 'copy_01269_no_such_file.csv';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '58P01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS rows_in_table FROM pg_catalog.pg_class WHERE relname = 'copy_01269_t' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
RESET search_path;
DROP ROLE IF EXISTS copy_01269_actor;
DROP TABLE IF EXISTS copy_01269_t;
