-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE CAST privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATECAST02631
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|02631|actual_cast_execution|DROP_CAST_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (createcast_02631_sourcetype AS bigint);
DROP CAST IF EXISTS (bigint AS createcast_02631_sourcetype);
DROP FUNCTION IF EXISTS createcast_02631_castfn;
DROP FUNCTION IF EXISTS createcast_02631_revcastfn;
DROP TYPE IF EXISTS createcast_02631_sourcetype;
DROP OWNED BY createcast_02631_actor CASCADE;
DROP ROLE IF EXISTS createcast_02631_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_02631_sourcetype AS ENUM ('a', 'b');
CREATE FUNCTION createcast_02631_castfn(createcast_02631_sourcetype) RETURNS bigint LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::bigint $$;
CREATE FUNCTION createcast_02631_revcastfn(bigint) RETURNS createcast_02631_sourcetype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::createcast_02631_sourcetype $$;
CREATE CAST (bigint AS createcast_02631_sourcetype) WITH FUNCTION createcast_02631_revcastfn;
CREATE ROLE createcast_02631_actor LOGIN NOSUPERUSER;
SET ROLE createcast_02631_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (createcast_02631_sourcetype AS bigint) WITH FUNCTION createcast_02631_castfn;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP CAST IF EXISTS (createcast_02631_sourcetype AS bigint);
DROP CAST IF EXISTS (bigint AS createcast_02631_sourcetype);
DROP FUNCTION IF EXISTS createcast_02631_castfn;
DROP FUNCTION IF EXISTS createcast_02631_revcastfn;
DROP TYPE IF EXISTS createcast_02631_sourcetype;
DROP OWNED BY createcast_02631_actor CASCADE;
DROP ROLE IF EXISTS createcast_02631_actor;
