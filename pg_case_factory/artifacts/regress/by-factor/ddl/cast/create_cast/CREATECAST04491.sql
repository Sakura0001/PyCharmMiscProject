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
-- case_id: CREATECAST04491
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|04491|actual_cast_execution|DROP_CAST_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42804
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (date AS createcast_04491_targettype);
DROP CAST IF EXISTS (createcast_04491_targettype AS date);
DROP FUNCTION IF EXISTS createcast_04491_castfn;
DROP FUNCTION IF EXISTS createcast_04491_revcastfn;
DROP TYPE IF EXISTS createcast_04491_targettype;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_04491_targettype AS ENUM ('a', 'b');
CREATE FUNCTION createcast_04491_castfn(createcast_04491_targettype) RETURNS createcast_04491_targettype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::createcast_04491_targettype $$;
CREATE FUNCTION createcast_04491_revcastfn(createcast_04491_targettype) RETURNS date LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::date $$;
CREATE CAST (createcast_04491_targettype AS date) WITH FUNCTION createcast_04491_revcastfn;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (date AS createcast_04491_targettype) WITH FUNCTION createcast_04491_castfn AS IMPLICIT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42804' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP CAST IF EXISTS (date AS createcast_04491_targettype);
DROP CAST IF EXISTS (createcast_04491_targettype AS date);
DROP FUNCTION IF EXISTS createcast_04491_castfn;
DROP FUNCTION IF EXISTS createcast_04491_revcastfn;
DROP TYPE IF EXISTS createcast_04491_targettype;
