-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : LISTEN target_action=listen
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: LISTEN00780
-- source_md: skills/pg-sql-generation/references/statements/session/notification/listen.md
-- factor_md: skills/pg-sql-generation/references/combinations/session/notification/listen.yaml
-- primary_obligation_id: LISTEN-EXT|00780|catalog_query|rollback|scope_value
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
UNLISTEN *;
RESET ROLE;
DROP ROLE IF EXISTS listen_00780_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE listen_00780_actor LOGIN NOSUPERUSER;
SET ROLE listen_00780_actor;
-- 3. 执行唯一获得覆盖信用的 LISTEN。
-- primary-target-begin
LISTEN listen_00780_ch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS listening FROM pg_catalog.pg_listening_channels() AS ch WHERE ch = 'listen_00780_ch' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
UNLISTEN *;
RESET ROLE;
DROP OWNED BY listen_00780_actor CASCADE;
DROP ROLE IF EXISTS listen_00780_actor;
