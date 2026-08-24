-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SERVER target_action=owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSERVER01021
-- source_md: skills/pg-sql-generation/references/statements/ddl/server/alter_server.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/server/alter_server.yaml
-- primary_obligation_id: ASRV-EXT|01021|pg_foreign_server_catalog|drop_server
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SERVER IF EXISTS alterserver_01021_srv CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterserver_01021_fdw CASCADE;
DROP FUNCTION IF EXISTS alterserver_01021_validator(text[], oid) CASCADE;
DROP OWNED BY alterserver_01021_srvowner CASCADE;
DROP ROLE IF EXISTS alterserver_01021_srvowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterserver_01021_srvowner LOGIN;
CREATE OR REPLACE FUNCTION alterserver_01021_validator(text[], oid) RETURNS void LANGUAGE plpgsql AS $body$ DECLARE item text; BEGIN FOREACH item IN ARRAY $1 LOOP IF pg_catalog.split_part(item, '=', 1) = 'invalid_option' THEN RAISE EXCEPTION 'invalid option %', item USING ERRCODE='HV00D'; END IF; END LOOP; END $body$;
CREATE FOREIGN DATA WRAPPER alterserver_01021_fdw VALIDATOR alterserver_01021_validator;
CREATE SERVER alterserver_01021_srv FOREIGN DATA WRAPPER alterserver_01021_fdw;
ALTER SERVER alterserver_01021_srv OWNER TO alterserver_01021_srvowner;
SET ROLE alterserver_01021_srvowner;
-- 3. 执行唯一获得覆盖信用的 ALTER SERVER。
-- primary-target-begin
ALTER SERVER alterserver_01021_srv OWNER TO CURRENT_ROLE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS server_state FROM pg_catalog.pg_foreign_server WHERE srvname = 'alterserver_01021_srv' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SERVER IF EXISTS alterserver_01021_srv CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterserver_01021_fdw CASCADE;
DROP FUNCTION IF EXISTS alterserver_01021_validator(text[], oid) CASCADE;
DROP OWNED BY alterserver_01021_srvowner CASCADE;
DROP ROLE IF EXISTS alterserver_01021_srvowner;
