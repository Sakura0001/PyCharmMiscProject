-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE OPERATOR target_object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEOPERATOR00967
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator/create_operator.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator/create_operator.yaml
-- primary_obligation_id: COP-EXT|00967|error_assertion|drop_objects|estimator_clauses
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS createoperator_00967_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createoperator_00967_schema;
CREATE FUNCTION createoperator_00967_schema.createoperator_00967_opfn(integer) RETURNS boolean AS 'SELECT true' LANGUAGE SQL IMMUTABLE;
CREATE OPERATOR createoperator_00967_schema.=== (FUNCTION = createoperator_00967_schema.createoperator_00967_opfn, RIGHTARG = integer);
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE OPERATOR。
-- primary-target-begin
CREATE OPERATOR createoperator_00967_schema.=== (FUNCTION = createoperator_00967_schema.createoperator_00967_opfn, RIGHTARG = integer, JOIN = pg_catalog.eqjoinsel, HASHES, MERGES);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP OPERATOR IF EXISTS createoperator_00967_schema.=== (integer) CASCADE;
DROP FUNCTION IF EXISTS createoperator_00967_schema.createoperator_00967_opfn CASCADE;
DROP SCHEMA IF EXISTS createoperator_00967_schema CASCADE;
