-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : VACUUM environment_context=transaction_block
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: VACUUM01338
-- source_md: skills/pg-sql-generation/references/statements/utility/maintenance/vacuum.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/maintenance/vacuum.yaml
-- primary_obligation_id: VACUUM-EXT|01338|error_assertion|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 25001
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS vacuum_01338_t CASCADE;
DROP SCHEMA IF EXISTS vacuum_01338_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA vacuum_01338_sch;
CREATE TABLE vacuum_01338_t (id integer);
INSERT INTO vacuum_01338_t (id) VALUES (1), (2);
BEGIN;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 VACUUM。
-- primary-target-begin
VACUUM vacuum_01338_sch.vacuum_01338_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
ROLLBACK;
SELECT :'target_sqlstate' = '25001' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS vacuum_01338_sch CASCADE;
DROP TABLE IF EXISTS vacuum_01338_t CASCADE;
