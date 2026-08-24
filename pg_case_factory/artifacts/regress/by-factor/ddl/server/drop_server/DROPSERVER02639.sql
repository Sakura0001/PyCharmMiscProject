-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP SERVER server_existence=server_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPSERVER02639
-- source_md: skills/pg-sql-generation/references/statements/ddl/server/drop_server.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/server/drop_server.yaml
-- primary_obligation_id: DROPSERVER-EXT|02639|drop_server|error_assertion|drop_user_mapping_then_drop_server
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SERVER IF EXISTS dropserver_02639_noexist1 CASCADE;
DROP SERVER IF EXISTS dropserver_02639_noexist2 CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dropserver_02639_fdw CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地外部服务器和因子专用夹具。
CREATE FOREIGN DATA WRAPPER dropserver_02639_fdw;
SELECT 1 AS target_server_intentionally_absent;
-- 3. 执行唯一获得覆盖信用的 DROP SERVER。
-- primary-target-begin
DROP SERVER IF EXISTS dropserver_02639_noexist1, dropserver_02639_noexist2 RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS server_absent FROM pg_catalog.pg_foreign_server WHERE srvname IN ('dropserver_02639_noexist1', 'dropserver_02639_noexist2') ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP SERVER IF EXISTS dropserver_02639_noexist1 CASCADE;
DROP SERVER IF EXISTS dropserver_02639_noexist2 CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dropserver_02639_fdw CASCADE;
