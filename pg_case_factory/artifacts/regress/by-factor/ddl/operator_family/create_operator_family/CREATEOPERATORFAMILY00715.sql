-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE OPERATOR FAMILY privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEOPERATORFAMILY00715
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_family/create_operator_family.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_family/create_operator_family.yaml
-- primary_obligation_id: COF-EXT|00715|error_assertion|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR FAMILY IF EXISTS createoperatorfamily_00715_opfam CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createoperatorfamily_00715_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createoperatorfamily_00715_actor LOGIN NOSUPERUSER;
SET ROLE createoperatorfamily_00715_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE OPERATOR FAMILY。
-- primary-target-begin
CREATE OPERATOR FAMILY createoperatorfamily_00715_opfam USING brin;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OPERATOR FAMILY IF EXISTS createoperatorfamily_00715_opfam CASCADE;
DROP OWNED BY createoperatorfamily_00715_actor CASCADE;
DROP ROLE IF EXISTS createoperatorfamily_00715_actor;
