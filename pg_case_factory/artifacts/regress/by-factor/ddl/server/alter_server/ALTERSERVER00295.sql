-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SERVER executor_privilege=non_owner_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSERVER00295
-- source_md: skills/pg-sql-generation/references/statements/ddl/server/alter_server.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/server/alter_server.yaml
-- primary_obligation_id: ASRV-EXT|00295|pg_foreign_server_options_query|drop_server
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SERVER IF EXISTS alterserver_00295_srv CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterserver_00295_fdw CASCADE;
DROP USER MAPPING IF EXISTS FOR CURRENT_USER SERVER alterserver_00295_srv;
DROP FUNCTION IF EXISTS alterserver_00295_validator(text[], oid) CASCADE;
DROP OWNED BY alterserver_00295_actor CASCADE;
DROP ROLE IF EXISTS alterserver_00295_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterserver_00295_srvowner LOGIN;
CREATE ROLE alterserver_00295_actor LOGIN NOSUPERUSER;
CREATE OR REPLACE FUNCTION alterserver_00295_validator(text[], oid) RETURNS void LANGUAGE plpgsql AS $body$ DECLARE item text; BEGIN FOREACH item IN ARRAY $1 LOOP IF pg_catalog.split_part(item, '=', 1) = 'invalid_option' THEN RAISE EXCEPTION 'invalid option %', item USING ERRCODE='HV00D'; END IF; END LOOP; END $body$;
CREATE FOREIGN DATA WRAPPER alterserver_00295_fdw VALIDATOR alterserver_00295_validator;
CREATE SERVER alterserver_00295_srv FOREIGN DATA WRAPPER alterserver_00295_fdw OPTIONS (opt1 'init1');
ALTER SERVER alterserver_00295_srv OWNER TO alterserver_00295_srvowner;
CREATE USER MAPPING FOR CURRENT_USER SERVER alterserver_00295_srv OPTIONS (user 'tester');
SET ROLE alterserver_00295_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SERVER。
-- primary-target-begin
ALTER SERVER alterserver_00295_srv VERSION NULL OPTIONS (DROP opt1);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS server_state FROM pg_catalog.pg_foreign_server WHERE srvname = 'alterserver_00295_srv' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SERVER IF EXISTS alterserver_00295_srv CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterserver_00295_fdw CASCADE;
DROP USER MAPPING IF EXISTS FOR CURRENT_USER SERVER alterserver_00295_srv;
DROP FUNCTION IF EXISTS alterserver_00295_validator(text[], oid) CASCADE;
DROP OWNED BY alterserver_00295_actor CASCADE;
DROP ROLE IF EXISTS alterserver_00295_actor;
