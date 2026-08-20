-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE OPERATOR privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEOPERATOR00202
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator/create_operator.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator/create_operator.yaml
-- primary_obligation_id: COP-EXT|00202|catalog_query|reset_state|core_clauses
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS createoperator_00202_schema CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createoperator_00202_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createoperator_00202_schema;
CREATE FUNCTION createoperator_00202_schema.createoperator_00202_opfn(integer) RETURNS boolean AS 'SELECT true' LANGUAGE SQL IMMUTABLE;
CREATE ROLE createoperator_00202_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA createoperator_00202_schema TO createoperator_00202_actor;
SET ROLE createoperator_00202_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE OPERATOR。
-- primary-target-begin
CREATE OPERATOR createoperator_00202_schema.=== (FUNCTION = createoperator_00202_schema.createoperator_00202_opfn, RIGHTARG = integer);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS operator_state FROM pg_catalog.pg_operator WHERE oprname = '===' AND oprnamespace = 'createoperator_00202_schema'::regnamespace ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
RESET ROLE;
DROP SCHEMA IF EXISTS createoperator_00202_schema CASCADE;
DROP OWNED BY createoperator_00202_actor CASCADE;
DROP ROLE IF EXISTS createoperator_00202_actor;
