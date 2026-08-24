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
-- case_id: CREATECAST16435
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|16435|actual_cast_execution|DROP_CAST_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (text AS createcast_16435_targettype);
DROP CAST IF EXISTS (createcast_16435_targettype AS text);
DROP FUNCTION IF EXISTS createcast_16435_revcastfn;
DROP TYPE IF EXISTS createcast_16435_targettype;
DROP OWNED BY createcast_16435_actor CASCADE;
DROP ROLE IF EXISTS createcast_16435_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_16435_targettype AS ENUM ('a', 'b');
CREATE CAST (createcast_16435_targettype AS text) WITH INOUT;
CREATE ROLE createcast_16435_actor LOGIN NOSUPERUSER;
SET ROLE createcast_16435_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (text AS createcast_16435_targettype) WITH INOUT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP CAST IF EXISTS (text AS createcast_16435_targettype);
DROP CAST IF EXISTS (createcast_16435_targettype AS text);
DROP FUNCTION IF EXISTS createcast_16435_revcastfn;
DROP TYPE IF EXISTS createcast_16435_targettype;
DROP OWNED BY createcast_16435_actor CASCADE;
DROP ROLE IF EXISTS createcast_16435_actor;
