-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE CAST function_dependency=function_exists_wrong_signature
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATECAST04805
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|04805|pg_cast_catalog_query|DROP_CAST_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42804
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (text AS createcast_04805_targettype);
DROP CAST IF EXISTS (createcast_04805_targettype AS text);
DROP FUNCTION IF EXISTS createcast_04805_castfn;
DROP FUNCTION IF EXISTS createcast_04805_revcastfn;
DROP TYPE IF EXISTS createcast_04805_targettype;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_04805_targettype AS ENUM ('a', 'b');
CREATE FUNCTION createcast_04805_castfn(createcast_04805_targettype) RETURNS createcast_04805_targettype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::createcast_04805_targettype $$;
CREATE FUNCTION createcast_04805_revcastfn(createcast_04805_targettype) RETURNS text LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::text $$;
CREATE CAST (createcast_04805_targettype AS text) WITH FUNCTION createcast_04805_revcastfn;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (text AS createcast_04805_targettype) WITH FUNCTION createcast_04805_castfn AS IMPLICIT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42804' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS cast_state FROM pg_catalog.pg_cast WHERE castsource = 'text'::regtype AND casttarget = 'createcast_04805_targettype'::regtype ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP CAST IF EXISTS (text AS createcast_04805_targettype);
DROP CAST IF EXISTS (createcast_04805_targettype AS text);
DROP FUNCTION IF EXISTS createcast_04805_castfn;
DROP FUNCTION IF EXISTS createcast_04805_revcastfn;
DROP TYPE IF EXISTS createcast_04805_targettype;
