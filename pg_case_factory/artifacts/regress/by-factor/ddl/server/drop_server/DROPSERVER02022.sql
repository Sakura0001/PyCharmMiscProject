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
-- case_id: DROPSERVER02022
-- source_md: skills/pg-sql-generation/references/statements/ddl/server/drop_server.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/server/drop_server.yaml
-- primary_obligation_id: DROPSERVER-EXT|02022|drop_server|error_assertion|drop_server_cascade
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SERVER IF EXISTS "user" CASCADE;
DROP SERVER IF EXISTS "order" CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dropserver_02022_fdw CASCADE;
DROP OWNED BY dropserver_02022_actor;
DROP ROLE IF EXISTS dropserver_02022_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地外部服务器和因子专用夹具。
CREATE ROLE dropserver_02022_actor LOGIN NOSUPERUSER;
CREATE FOREIGN DATA WRAPPER dropserver_02022_fdw;
CREATE SERVER "user" FOREIGN DATA WRAPPER dropserver_02022_fdw;
CREATE SERVER "order" FOREIGN DATA WRAPPER dropserver_02022_fdw;
SET ROLE dropserver_02022_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP SERVER。
-- primary-target-begin
DROP SERVER IF EXISTS "user", "order" RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS server_present FROM pg_catalog.pg_foreign_server WHERE srvname IN ('user', 'order') ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SERVER IF EXISTS "user" CASCADE;
DROP SERVER IF EXISTS "order" CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dropserver_02022_fdw CASCADE;
DROP OWNED BY dropserver_02022_actor;
DROP ROLE IF EXISTS dropserver_02022_actor;
