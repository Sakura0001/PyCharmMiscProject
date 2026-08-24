-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE COLLATION privilege_level=non_schema_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATECOLLATION01059
-- source_md: skills/pg-sql-generation/references/statements/ddl/collation/create_collation.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/collation/create_collation.yaml
-- primary_obligation_id: CCOL-EXT|01059|pg_collation_catalog_query|DROP_COLLATION_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP COLLATION IF EXISTS public.createcollation_01059_col CASCADE;
DROP COLLATION IF EXISTS createcollation_01059_src CASCADE;
DROP COLLATION IF EXISTS createcollation_01059_nosuch CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createcollation_01059_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createcollation_01059_actor LOGIN NOSUPERUSER;
CREATE COLLATION createcollation_01059_src FROM "C";
SET ROLE createcollation_01059_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE COLLATION。
-- primary-target-begin
CREATE COLLATION IF NOT EXISTS public.createcollation_01059_col FROM createcollation_01059_src;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS collation_state FROM pg_catalog.pg_collation WHERE collname = 'createcollation_01059_col' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP COLLATION IF EXISTS public.createcollation_01059_col;
DROP COLLATION IF EXISTS createcollation_01059_src;
DROP OWNED BY createcollation_01059_actor CASCADE;
DROP ROLE IF EXISTS createcollation_01059_actor;
