-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : DROP CAST privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPCAST00113
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/drop_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/drop_cast.yaml
-- primary_obligation_id: DCAST-EXT|00113|drop_cast|pg_cast_catalog_query|DROP_CAST_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (dropcast_00113_sourcetype AS dropcast_00113_targettype);
DROP FUNCTION IF EXISTS dropcast_00113_castfn;
DROP TYPE IF EXISTS dropcast_00113_sourcetype;
DROP TYPE IF EXISTS dropcast_00113_targettype;
DROP ROLE IF EXISTS dropcast_00113_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地类型和因子专用夹具。
CREATE TYPE dropcast_00113_sourcetype AS ENUM ('a', 'b');
CREATE TYPE dropcast_00113_targettype AS ENUM ('a', 'b');
CREATE ROLE dropcast_00113_actor LOGIN NOSUPERUSER;
CREATE FUNCTION dropcast_00113_castfn(dropcast_00113_sourcetype) RETURNS dropcast_00113_targettype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::dropcast_00113_targettype $$;
CREATE CAST (dropcast_00113_sourcetype AS dropcast_00113_targettype) WITH FUNCTION dropcast_00113_castfn;
SET ROLE dropcast_00113_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP CAST。
-- primary-target-begin
DROP CAST (dropcast_00113_sourcetype AS dropcast_00113_targettype) RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS cast_present FROM pg_catalog.pg_cast WHERE castsource = 'dropcast_00113_sourcetype'::regtype AND casttarget = 'dropcast_00113_targettype'::regtype ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP CAST IF EXISTS (dropcast_00113_sourcetype AS dropcast_00113_targettype);
DROP FUNCTION IF EXISTS dropcast_00113_castfn;
DROP TYPE IF EXISTS dropcast_00113_sourcetype;
DROP TYPE IF EXISTS dropcast_00113_targettype;
DROP OWNED BY dropcast_00113_actor CASCADE;
DROP ROLE IF EXISTS dropcast_00113_actor;
