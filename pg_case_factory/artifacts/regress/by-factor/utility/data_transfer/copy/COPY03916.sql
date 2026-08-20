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
-- case_id: COPY03916
-- source_md: skills/pg-sql-generation/references/statements/utility/data_transfer/copy.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/data_transfer/copy.yaml
-- primary_obligation_id: COPY-EXT|03916|catalog_query|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 0A000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS copy_03916_t;
DROP ROLE IF EXISTS copy_03916_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE copy_03916_actor LOGIN NOSUPERUSER;
CREATE TABLE copy_03916_t (copy_03916_c int);
GRANT SELECT, INSERT ON copy_03916_t TO copy_03916_actor;
SET ROLE copy_03916_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 COPY。
-- primary-target-begin
COPY copy_03916_t (copy_03916_c) TO STDOUT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '0A000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS database_wide_marker FROM pg_catalog.pg_class WHERE relname = 'copy_03916_t' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
ROLLBACK;
DROP ROLE IF EXISTS copy_03916_actor;
DROP TABLE IF EXISTS copy_03916_t;
