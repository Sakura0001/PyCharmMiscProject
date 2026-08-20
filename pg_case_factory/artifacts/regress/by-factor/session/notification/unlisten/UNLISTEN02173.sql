-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : UNLISTEN target_action=unlisten
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: UNLISTEN02173
-- source_md: skills/pg-sql-generation/references/statements/session/notification/unlisten.md
-- factor_md: skills/pg-sql-generation/references/combinations/session/notification/unlisten.yaml
-- primary_obligation_id: UNLISTEN-EXT|02173|error_assertion|reset_state|scope_name
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
UNLISTEN *;
RESET ROLE;
DROP ROLE IF EXISTS unlisten_02173_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
LISTEN unlisten_02173_ch;
CREATE ROLE unlisten_02173_actor LOGIN NOSUPERUSER;
SET ROLE unlisten_02173_actor;
-- 3. 执行唯一获得覆盖信用的 UNLISTEN。
-- primary-target-begin
UNLISTEN unlisten_02173_ch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
UNLISTEN *;
RESET ROLE;
DROP OWNED BY unlisten_02173_actor CASCADE;
DROP ROLE IF EXISTS unlisten_02173_actor;
