-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE SERVER server_identity=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATESERVER03515
-- source_md: skills/pg-sql-generation/references/statements/ddl/server/create_server.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/server/create_server.yaml
-- primary_obligation_id: CSRV-EXT|03515|error_assertion|drop_fdw_then_drop_server
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SERVER IF EXISTS "createserver_03515_Mixed Srv" CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createserver_03515_fdw CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FOREIGN DATA WRAPPER createserver_03515_fdw;
CREATE SERVER "createserver_03515_Mixed Srv" FOREIGN DATA WRAPPER createserver_03515_fdw;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE SERVER。
-- primary-target-begin
CREATE SERVER "createserver_03515_Mixed Srv" VERSION 'createserver_03515_srvver' FOREIGN DATA WRAPPER createserver_03515_fdw;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP SERVER IF EXISTS "createserver_03515_Mixed Srv" CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createserver_03515_fdw CASCADE;
