-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE SERVER executor_privilege=non_superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATESERVER00447
-- source_md: skills/pg-sql-generation/references/statements/ddl/server/create_server.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/server/create_server.yaml
-- primary_obligation_id: CSRV-EXT|00447|error_assertion|drop_fdw_then_drop_server
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SERVER IF EXISTS createserver_00447_srv CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createserver_00447_fdw CASCADE;
DROP OWNED BY createserver_00447_actor CASCADE;
DROP ROLE IF EXISTS createserver_00447_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createserver_00447_actor LOGIN NOSUPERUSER;
CREATE FOREIGN DATA WRAPPER createserver_00447_fdw;
SET ROLE createserver_00447_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE SERVER。
-- primary-target-begin
CREATE SERVER createserver_00447_srv TYPE 'createserver_00447_srvtype' VERSION 'createserver_00447_srvver' FOREIGN DATA WRAPPER createserver_00447_fdw OPTIONS ('createserver_00447_opt1' 'createserver_00447_optval');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SERVER IF EXISTS createserver_00447_srv CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createserver_00447_fdw CASCADE;
DROP OWNED BY createserver_00447_actor CASCADE;
DROP ROLE IF EXISTS createserver_00447_actor;
