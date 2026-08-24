-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : UNLISTEN expected_status=failure
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: UNLISTEN00004
-- source_md: skills/pg-sql-generation/references/statements/session/notification/unlisten.md
-- factor_md: skills/pg-sql-generation/references/combinations/session/notification/unlisten.yaml
-- primary_obligation_id: UNLISTEN-SFV|sfv-6c528e3568449df67d8fc7f2|unlisten
-- expected_outcome: expected_failure
-- expected_sqlstate: 42601
-- 1. 清理本编号对象，保证脚本可重复执行。
UNLISTEN *;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 UNLISTEN。
-- primary-target-begin
UNLISTEN ;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42601' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS not_listening FROM pg_catalog.pg_listening_channels() AS ch WHERE ch = 'unlisten_00004_ch' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
UNLISTEN *;
