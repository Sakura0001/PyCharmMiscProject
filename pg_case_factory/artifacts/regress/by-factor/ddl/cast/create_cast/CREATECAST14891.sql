-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE CAST target_action=with_function
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATECAST14891
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|14891|actual_cast_execution|DROP_CAST_IF_EXISTS
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (bigint AS createcast_14891_targettype);
DROP CAST IF EXISTS (createcast_14891_targettype AS bigint);
DROP FUNCTION IF EXISTS public.createcast_14891_castfn;
DROP FUNCTION IF EXISTS createcast_14891_revcastfn;
DROP TYPE IF EXISTS createcast_14891_targettype;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_14891_targettype AS ENUM ('a', 'b');
CREATE FUNCTION public.createcast_14891_castfn(bigint) RETURNS createcast_14891_targettype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::createcast_14891_targettype $$;
CREATE FUNCTION createcast_14891_revcastfn(createcast_14891_targettype) RETURNS bigint LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::bigint $$;
CREATE CAST (createcast_14891_targettype AS bigint) WITH FUNCTION createcast_14891_revcastfn;
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (bigint AS createcast_14891_targettype) WITH FUNCTION public.createcast_14891_castfn AS IMPLICIT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT NULL::bigint::createcast_14891_targettype AS cast_execution_check;
-- 5. 清理全部本编号对象。
DROP CAST IF EXISTS (bigint AS createcast_14891_targettype);
DROP CAST IF EXISTS (createcast_14891_targettype AS bigint);
DROP FUNCTION IF EXISTS public.createcast_14891_castfn;
DROP FUNCTION IF EXISTS createcast_14891_revcastfn;
DROP TYPE IF EXISTS createcast_14891_targettype;
