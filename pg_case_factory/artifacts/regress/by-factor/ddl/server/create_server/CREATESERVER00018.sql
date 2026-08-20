-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE SERVER fdw_validator_rejection=validator_rejects_invalid_option
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATESERVER00018
-- source_md: skills/pg-sql-generation/references/statements/ddl/server/create_server.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/server/create_server.yaml
-- primary_obligation_id: CSRV-SFV|sfv-e5907b8f510d54641c3026d4|create_server
-- expected_outcome: expected_failure
-- expected_sqlstate: HV000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SERVER IF EXISTS createserver_00018_srv CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createserver_00018_fdw CASCADE;
DROP FUNCTION IF EXISTS createserver_00018_validator(text[], oid);
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createserver_00018_validator(text[], oid) RETURNS void LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'invalid option'; END; $$;
CREATE FOREIGN DATA WRAPPER createserver_00018_fdw VALIDATOR createserver_00018_validator;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE SERVER。
-- primary-target-begin
CREATE SERVER createserver_00018_srv FOREIGN DATA WRAPPER createserver_00018_fdw;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = 'HV000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS server_state FROM pg_catalog.pg_foreign_server WHERE srvname = 'createserver_00018_srv' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP SERVER IF EXISTS createserver_00018_srv CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createserver_00018_fdw CASCADE;
DROP FUNCTION IF EXISTS createserver_00018_validator(text[], oid);
