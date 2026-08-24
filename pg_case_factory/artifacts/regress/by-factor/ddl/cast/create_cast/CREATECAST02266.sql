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
-- case_id: CREATECAST02266
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|02266|actual_cast_execution|DROP_CAST
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (numeric AS boolean);
DROP CAST IF EXISTS (boolean AS numeric);
DROP FUNCTION IF EXISTS createcast_02266_castfn;
DROP FUNCTION IF EXISTS createcast_02266_revcastfn;
DROP OWNED BY createcast_02266_actor CASCADE;
DROP ROLE IF EXISTS createcast_02266_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createcast_02266_castfn(numeric) RETURNS boolean LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::boolean $$;
CREATE FUNCTION createcast_02266_revcastfn(boolean) RETURNS numeric LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::numeric $$;
CREATE CAST (boolean AS numeric) WITH FUNCTION createcast_02266_revcastfn;
CREATE ROLE createcast_02266_actor LOGIN NOSUPERUSER;
SET ROLE createcast_02266_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (numeric AS boolean) WITH FUNCTION createcast_02266_castfn AS ASSIGNMENT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP CAST (numeric AS boolean);
DROP CAST (boolean AS numeric);
DROP FUNCTION IF EXISTS createcast_02266_castfn;
DROP FUNCTION IF EXISTS createcast_02266_revcastfn;
DROP OWNED BY createcast_02266_actor CASCADE;
DROP ROLE IF EXISTS createcast_02266_actor;
