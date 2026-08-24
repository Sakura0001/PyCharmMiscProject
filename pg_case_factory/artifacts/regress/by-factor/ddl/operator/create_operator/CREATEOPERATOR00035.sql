-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE OPERATOR operand_data_type=numeric
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEOPERATOR00035
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator/create_operator.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator/create_operator.yaml
-- primary_obligation_id: COP-SFV|sfv-4d2d0d0aa3465a9766ef74ba|define_operator
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS createoperator_00035_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createoperator_00035_schema;
CREATE FUNCTION createoperator_00035_schema.createoperator_00035_opfn(numeric, numeric) RETURNS boolean AS 'SELECT true' LANGUAGE SQL IMMUTABLE;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE OPERATOR。
-- primary-target-begin
CREATE OPERATOR createoperator_00035_schema.=== (FUNCTION = createoperator_00035_schema.createoperator_00035_opfn, LEFTARG = numeric, RIGHTARG = numeric);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS operator_state FROM pg_catalog.pg_operator WHERE oprname = '===' AND oprnamespace = 'createoperator_00035_schema'::regnamespace AND oprright = 'numeric'::regtype ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP OPERATOR IF EXISTS createoperator_00035_schema.=== (numeric, numeric) CASCADE;
DROP FUNCTION IF EXISTS createoperator_00035_schema.createoperator_00035_opfn CASCADE;
DROP SCHEMA IF EXISTS createoperator_00035_schema CASCADE;
