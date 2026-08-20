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
-- case_id: CREATECAST02724
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|02724|pg_cast_catalog_query|DROP_CAST
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (numeric AS createcast_02724_targettype);
DROP CAST IF EXISTS (createcast_02724_targettype AS numeric);
DROP FUNCTION IF EXISTS createcast_02724_castfn;
DROP FUNCTION IF EXISTS createcast_02724_revcastfn;
DROP TYPE IF EXISTS createcast_02724_targettype;
DROP OWNED BY createcast_02724_actor CASCADE;
DROP ROLE IF EXISTS createcast_02724_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_02724_targettype AS ENUM ('a', 'b');
CREATE FUNCTION createcast_02724_castfn(numeric) RETURNS createcast_02724_targettype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::createcast_02724_targettype $$;
CREATE FUNCTION createcast_02724_revcastfn(createcast_02724_targettype) RETURNS numeric LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::numeric $$;
CREATE CAST (createcast_02724_targettype AS numeric) WITH FUNCTION createcast_02724_revcastfn;
CREATE ROLE createcast_02724_actor LOGIN NOSUPERUSER;
SET ROLE createcast_02724_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (numeric AS createcast_02724_targettype) WITH FUNCTION createcast_02724_castfn;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS cast_state FROM pg_catalog.pg_cast WHERE castsource = 'numeric'::regtype AND casttarget = 'createcast_02724_targettype'::regtype ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP CAST (numeric AS createcast_02724_targettype);
DROP CAST (createcast_02724_targettype AS numeric);
DROP FUNCTION IF EXISTS createcast_02724_castfn;
DROP FUNCTION IF EXISTS createcast_02724_revcastfn;
DROP TYPE IF EXISTS createcast_02724_targettype;
DROP OWNED BY createcast_02724_actor CASCADE;
DROP ROLE IF EXISTS createcast_02724_actor;
