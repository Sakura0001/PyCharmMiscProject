-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : COPY target_state=database_wide
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: COPY02933
-- source_md: skills/pg-sql-generation/references/statements/utility/data_transfer/copy.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/data_transfer/copy.yaml
-- primary_obligation_id: COPY-EXT|02933|catalog_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 0A000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS copy_02933_t;
DROP ROLE IF EXISTS copy_02933_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE copy_02933_actor LOGIN NOSUPERUSER;
CREATE TABLE copy_02933_t (copy_02933_c int);
INSERT INTO copy_02933_t VALUES (1), (2), (3);
GRANT SELECT, INSERT ON copy_02933_t TO copy_02933_actor;
SET ROLE copy_02933_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 COPY。
-- primary-target-begin
COPY copy_02933_t TO 'copy_02933_out.csv';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '0A000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS database_wide_marker FROM pg_catalog.pg_class WHERE relname = 'copy_02933_t' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS copy_02933_actor;
DROP TABLE IF EXISTS copy_02933_t;
