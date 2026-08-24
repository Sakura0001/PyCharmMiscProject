-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE ROLE role_name_shape=mixed_case_id
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEROLE00080
-- source_md: skills/pg-sql-generation/references/statements/ddl/role/create_role.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/role/create_role.yaml
-- primary_obligation_id: CRP-SFV|sfv-f04184a6fd28741b56b7be02|create_role_branch_1
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS "createrole_00080_Mixed" CASCADE;
DROP ROLE IF EXISTS createrole_00080_ref CASCADE;
DROP ROLE IF EXISTS createrole_00080_ref1 CASCADE;
DROP ROLE IF EXISTS createrole_00080_ref2 CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE ROLE。
-- primary-target-begin
CREATE ROLE "createrole_00080_Mixed" WITH NOSUPERUSER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS role_state FROM pg_catalog.pg_roles WHERE rolname = 'createrole_00080_Mixed' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP ROLE IF EXISTS "createrole_00080_Mixed";
DROP ROLE IF EXISTS createrole_00080_ref;
SELECT 1 AS residual_check_no_objects;
