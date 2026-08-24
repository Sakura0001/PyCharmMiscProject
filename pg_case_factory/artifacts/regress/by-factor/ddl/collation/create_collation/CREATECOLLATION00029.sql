-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE COLLATION insufficient_privilege=no_create_on_schema
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATECOLLATION00029
-- source_md: skills/pg-sql-generation/references/statements/ddl/collation/create_collation.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/collation/create_collation.yaml
-- primary_obligation_id: CCOL-SFV|sfv-0f737fe2d1932b3e4453cfce|define_with_params
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP COLLATION IF EXISTS createcollation_00029_col CASCADE;
DROP COLLATION IF EXISTS createcollation_00029_src CASCADE;
DROP COLLATION IF EXISTS createcollation_00029_nosuch CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createcollation_00029_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createcollation_00029_actor LOGIN NOSUPERUSER;
SET ROLE createcollation_00029_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE COLLATION。
-- primary-target-begin
CREATE COLLATION createcollation_00029_col (LOCALE = 'C');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS collation_state FROM pg_catalog.pg_collation WHERE collname = 'createcollation_00029_col' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP COLLATION IF EXISTS createcollation_00029_col;
DROP OWNED BY createcollation_00029_actor CASCADE;
DROP ROLE IF EXISTS createcollation_00029_actor;
