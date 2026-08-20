-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : RELEASE SAVEPOINT target_action=release_savepoint
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: RELEASESAVEPOINT00904
-- source_md: skills/pg-sql-generation/references/statements/tcl/savepoint/release_savepoint.md
-- factor_md: skills/pg-sql-generation/references/combinations/tcl/savepoint/release_savepoint.yaml
-- primary_obligation_id: RELEASESAVEPOINT-EXT|00904|returned_rows|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
ROLLBACK;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
BEGIN;
SAVEPOINT releasesavepoint_00904_sp;
-- 3. 执行唯一获得覆盖信用的 RELEASE SAVEPOINT。
-- primary-target-begin
RELEASE SAVEPOINT releasesavepoint_00904_sp AND NO CHAIN;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT 1 AS release_savepoint_completed;
-- 5. 清理全部本编号对象。
ROLLBACK;
