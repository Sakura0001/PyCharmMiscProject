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
-- case_id: CREATESERVER00938
-- source_md: skills/pg-sql-generation/references/statements/ddl/server/create_server.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/server/create_server.yaml
-- primary_obligation_id: CSRV-EXT|00938|error_assertion|drop_server
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SERVER IF EXISTS createserver_00938_srv CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createserver_00938_fdw CASCADE;
DROP OWNED BY createserver_00938_actor CASCADE;
DROP ROLE IF EXISTS createserver_00938_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createserver_00938_actor LOGIN NOSUPERUSER;
CREATE FOREIGN DATA WRAPPER createserver_00938_fdw;
SET ROLE createserver_00938_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE SERVER。
-- primary-target-begin
CREATE SERVER IF NOT EXISTS createserver_00938_srv VERSION 'createserver_00938_srvver' FOREIGN DATA WRAPPER createserver_00938_fdw OPTIONS ('createserver_00938_opt1' 'createserver_00938_optval');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SERVER IF EXISTS createserver_00938_srv CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createserver_00938_fdw CASCADE;
DROP OWNED BY createserver_00938_actor CASCADE;
DROP ROLE IF EXISTS createserver_00938_actor;
