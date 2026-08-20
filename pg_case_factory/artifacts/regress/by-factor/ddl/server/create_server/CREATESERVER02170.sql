-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE SERVER target_action=create_server
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATESERVER02170
-- source_md: skills/pg-sql-generation/references/statements/ddl/server/create_server.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/server/create_server.yaml
-- primary_obligation_id: CSRV-EXT|02170|error_assertion|drop_server
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SERVER IF EXISTS "createserver_02170_select" CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createserver_02170_fdw CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FOREIGN DATA WRAPPER createserver_02170_fdw;
-- 3. 执行唯一获得覆盖信用的 CREATE SERVER。
-- primary-target-begin
CREATE SERVER "createserver_02170_select" VERSION 'createserver_02170_srvver' FOREIGN DATA WRAPPER createserver_02170_fdw OPTIONS ('createserver_02170_opt1' '');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP SERVER IF EXISTS "createserver_02170_select" CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createserver_02170_fdw CASCADE;
