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
-- case_id: CREATECOLLATION00583
-- source_md: skills/pg-sql-generation/references/statements/ddl/collation/create_collation.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/collation/create_collation.yaml
-- primary_obligation_id: CCOL-EXT|00583|actual_collation_usage|DROP_COLLATION_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP COLLATION IF EXISTS "createcollation_00583_QCol" CASCADE;
DROP COLLATION IF EXISTS createcollation_00583_src CASCADE;
DROP COLLATION IF EXISTS createcollation_00583_nosuch CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createcollation_00583_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createcollation_00583_actor LOGIN NOSUPERUSER;
SET ROLE createcollation_00583_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE COLLATION。
-- primary-target-begin
CREATE COLLATION IF NOT EXISTS "createcollation_00583_QCol" (LOCALE = 'C', PROVIDER = icu);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP COLLATION "createcollation_00583_QCol" CASCADE;
DROP OWNED BY createcollation_00583_actor CASCADE;
DROP ROLE IF EXISTS createcollation_00583_actor;
