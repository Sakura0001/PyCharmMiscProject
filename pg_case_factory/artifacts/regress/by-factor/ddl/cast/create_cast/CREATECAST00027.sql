-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE CAST object_state=not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATECAST00027
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-SFV|sfv-36118d0323ef194a45e7acfa|with_function
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (integer AS bigint);
DROP CAST IF EXISTS (bigint AS integer);
DROP FUNCTION IF EXISTS createcast_00027_castfn;
DROP FUNCTION IF EXISTS createcast_00027_revcastfn;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createcast_00027_castfn(integer) RETURNS bigint LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::bigint $$;
CREATE FUNCTION createcast_00027_revcastfn(bigint) RETURNS integer LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::integer $$;
CREATE CAST (bigint AS integer) WITH FUNCTION createcast_00027_revcastfn;
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (integer AS bigint) WITH FUNCTION createcast_00027_castfn;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS cast_state FROM pg_catalog.pg_cast WHERE castsource = 'integer'::regtype AND casttarget = 'bigint'::regtype ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP CAST (integer AS bigint);
DROP CAST (bigint AS integer);
DROP FUNCTION IF EXISTS createcast_00027_castfn;
DROP FUNCTION IF EXISTS createcast_00027_revcastfn;
