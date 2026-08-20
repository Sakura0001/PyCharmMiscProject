-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : NOTIFY payload_shape=boundary_length
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: NOTIFY01126
-- source_md: skills/pg-sql-generation/references/statements/session/notification/notify.md
-- factor_md: skills/pg-sql-generation/references/combinations/session/notification/notify.yaml
-- primary_obligation_id: NOTIFY-EXT|01126|error_assertion|rollback|name_payload
-- expected_outcome: expected_failure
-- expected_sqlstate: 08P01
-- 1. 清理本编号对象，保证脚本可重复执行。
UNLISTEN *;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 NOTIFY。
-- primary-target-begin
NOTIFY aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '08P01' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
UNLISTEN *;
