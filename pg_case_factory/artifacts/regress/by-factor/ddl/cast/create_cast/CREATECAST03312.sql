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
-- case_id: CREATECAST03312
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|03312|pg_cast_catalog_query|DROP_CAST
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (createcast_03312_sourcetype AS bigint);
DROP CAST IF EXISTS (bigint AS createcast_03312_sourcetype);
DROP FUNCTION IF EXISTS public.createcast_03312_castfn;
DROP FUNCTION IF EXISTS createcast_03312_revcastfn;
DROP TYPE IF EXISTS createcast_03312_sourcetype;
DROP OWNED BY createcast_03312_actor CASCADE;
DROP ROLE IF EXISTS createcast_03312_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_03312_sourcetype AS ENUM ('a', 'b');
CREATE FUNCTION public.createcast_03312_castfn(createcast_03312_sourcetype) RETURNS bigint LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::bigint $$;
CREATE FUNCTION createcast_03312_revcastfn(bigint) RETURNS createcast_03312_sourcetype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::createcast_03312_sourcetype $$;
CREATE CAST (bigint AS createcast_03312_sourcetype) WITH FUNCTION createcast_03312_revcastfn;
CREATE ROLE createcast_03312_actor LOGIN NOSUPERUSER;
SET ROLE createcast_03312_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (createcast_03312_sourcetype AS bigint) WITH FUNCTION public.createcast_03312_castfn;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS cast_state FROM pg_catalog.pg_cast WHERE castsource = 'createcast_03312_sourcetype'::regtype AND casttarget = 'bigint'::regtype ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP CAST (createcast_03312_sourcetype AS bigint);
DROP CAST (bigint AS createcast_03312_sourcetype);
DROP FUNCTION IF EXISTS public.createcast_03312_castfn;
DROP FUNCTION IF EXISTS createcast_03312_revcastfn;
DROP TYPE IF EXISTS createcast_03312_sourcetype;
DROP OWNED BY createcast_03312_actor CASCADE;
DROP ROLE IF EXISTS createcast_03312_actor;
