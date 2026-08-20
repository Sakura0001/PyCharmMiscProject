-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP SERVER privilege_context=non_owner_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPSERVER00176
-- source_md: skills/pg-sql-generation/references/statements/ddl/server/drop_server.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/server/drop_server.yaml
-- primary_obligation_id: DROPSERVER-EXT|00176|drop_server|pg_foreign_server_catalog|drop_server_cascade
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP USER MAPPING IF EXISTS FOR public SERVER "dropserver_00176_Qsrv";
DROP SERVER IF EXISTS "dropserver_00176_Qsrv" CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dropserver_00176_fdw CASCADE;
DROP OWNED BY dropserver_00176_actor;
DROP ROLE IF EXISTS dropserver_00176_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地外部服务器和因子专用夹具。
CREATE ROLE dropserver_00176_actor LOGIN NOSUPERUSER;
CREATE FOREIGN DATA WRAPPER dropserver_00176_fdw;
CREATE SERVER "dropserver_00176_Qsrv" FOREIGN DATA WRAPPER dropserver_00176_fdw;
CREATE USER MAPPING FOR public SERVER "dropserver_00176_Qsrv";
SET ROLE dropserver_00176_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP SERVER。
-- primary-target-begin
DROP SERVER IF EXISTS "dropserver_00176_Qsrv" CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS server_present FROM pg_catalog.pg_foreign_server WHERE srvname = 'dropserver_00176_Qsrv' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP USER MAPPING IF EXISTS FOR public SERVER "dropserver_00176_Qsrv";
DROP SERVER IF EXISTS "dropserver_00176_Qsrv" CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dropserver_00176_fdw CASCADE;
DROP OWNED BY dropserver_00176_actor;
DROP ROLE IF EXISTS dropserver_00176_actor;
