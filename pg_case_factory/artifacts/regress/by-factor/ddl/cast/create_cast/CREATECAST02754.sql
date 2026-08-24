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
-- case_id: CREATECAST02754
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|02754|actual_cast_execution|DROP_CAST
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (text AS createcast_02754_targettype);
DROP CAST IF EXISTS (createcast_02754_targettype AS text);
DROP FUNCTION IF EXISTS createcast_02754_castfn;
DROP FUNCTION IF EXISTS createcast_02754_revcastfn;
DROP TYPE IF EXISTS createcast_02754_targettype;
DROP OWNED BY createcast_02754_actor CASCADE;
DROP ROLE IF EXISTS createcast_02754_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_02754_targettype AS ENUM ('a', 'b');
CREATE FUNCTION createcast_02754_castfn(text) RETURNS createcast_02754_targettype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::createcast_02754_targettype $$;
CREATE FUNCTION createcast_02754_revcastfn(createcast_02754_targettype) RETURNS text LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::text $$;
CREATE CAST (createcast_02754_targettype AS text) WITH FUNCTION createcast_02754_revcastfn;
CREATE ROLE createcast_02754_actor LOGIN NOSUPERUSER;
SET ROLE createcast_02754_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (text AS createcast_02754_targettype) WITH FUNCTION createcast_02754_castfn;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP CAST (text AS createcast_02754_targettype);
DROP CAST (createcast_02754_targettype AS text);
DROP FUNCTION IF EXISTS createcast_02754_castfn;
DROP FUNCTION IF EXISTS createcast_02754_revcastfn;
DROP TYPE IF EXISTS createcast_02754_targettype;
DROP OWNED BY createcast_02754_actor CASCADE;
DROP ROLE IF EXISTS createcast_02754_actor;
