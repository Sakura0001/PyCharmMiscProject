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
-- case_id: CREATECAST02420
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|02420|pg_cast_catalog_query|DROP_CAST
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (createcast_02420_sourcetype AS text);
DROP CAST IF EXISTS (text AS createcast_02420_sourcetype);
DROP FUNCTION IF EXISTS createcast_02420_castfn;
DROP FUNCTION IF EXISTS createcast_02420_revcastfn;
DROP TYPE IF EXISTS createcast_02420_sourcetype;
DROP OWNED BY createcast_02420_actor CASCADE;
DROP ROLE IF EXISTS createcast_02420_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_02420_sourcetype AS ENUM ('a', 'b');
CREATE FUNCTION createcast_02420_castfn(createcast_02420_sourcetype) RETURNS text LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::text $$;
CREATE FUNCTION createcast_02420_revcastfn(text) RETURNS createcast_02420_sourcetype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::createcast_02420_sourcetype $$;
CREATE CAST (text AS createcast_02420_sourcetype) WITH FUNCTION createcast_02420_revcastfn;
CREATE ROLE createcast_02420_actor LOGIN NOSUPERUSER;
SET ROLE createcast_02420_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (createcast_02420_sourcetype AS text) WITH FUNCTION createcast_02420_castfn AS IMPLICIT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS cast_state FROM pg_catalog.pg_cast WHERE castsource = 'createcast_02420_sourcetype'::regtype AND casttarget = 'text'::regtype ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP CAST (createcast_02420_sourcetype AS text);
DROP CAST (text AS createcast_02420_sourcetype);
DROP FUNCTION IF EXISTS createcast_02420_castfn;
DROP FUNCTION IF EXISTS createcast_02420_revcastfn;
DROP TYPE IF EXISTS createcast_02420_sourcetype;
DROP OWNED BY createcast_02420_actor CASCADE;
DROP ROLE IF EXISTS createcast_02420_actor;
