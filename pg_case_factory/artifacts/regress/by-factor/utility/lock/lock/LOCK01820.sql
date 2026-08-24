-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : LOCK TABLE statement_branch=branch_1
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: LOCK01820
-- source_md: skills/pg-sql-generation/references/statements/utility/lock/lock.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/lock/lock.yaml
-- primary_obligation_id: LOCK-EXT|01820|returned_rows|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS lock_01820_t CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE lock_01820_t (c integer);
-- 3. 执行唯一获得覆盖信用的 LOCK TABLE。
-- primary-target-begin
LOCK TABLE lock_01820_t IN ACCESS EXCLUSIVE MODE NOWAIT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS lock_state_rows FROM pg_catalog.pg_locks WHERE granted IS NOT NULL ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS lock_01820_t CASCADE;
