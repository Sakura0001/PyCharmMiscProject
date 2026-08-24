-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP OPERATOR privilege_context=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPOPERATOR01293
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator/drop_operator.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator/drop_operator.yaml
-- primary_obligation_id: DROPOPERATOR-EXT|01293|drop_operator|catalog_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR IF EXISTS dropoperator_01293_op (integer, integer) CASCADE;
DROP FUNCTION IF EXISTS dropoperator_01293_opfn;
DROP OWNED BY dropoperator_01293_actor;
DROP ROLE IF EXISTS dropoperator_01293_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地 operator 和因子专用夹具。
CREATE ROLE dropoperator_01293_actor LOGIN NOSUPERUSER;
CREATE FUNCTION dropoperator_01293_opfn(integer, integer) RETURNS integer AS $$ SELECT $1; $$ LANGUAGE immutable;
CREATE OPERATOR dropoperator_01293_op (PROCEDURE = dropoperator_01293_opfn, LEFTARG = integer, RIGHTARG = integer);
SET ROLE dropoperator_01293_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP OPERATOR。
-- primary-target-begin
DROP OPERATOR IF EXISTS dropoperator_01293_op (integer, integer);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS operator_present FROM pg_catalog.pg_operator WHERE oprname = 'dropoperator_01293_op' AND oprleft = 'integer'::regtype AND oprright = 'integer'::regtype ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OPERATOR IF EXISTS dropoperator_01293_op (integer, integer) CASCADE;
DROP FUNCTION IF EXISTS dropoperator_01293_opfn;
DROP OWNED BY dropoperator_01293_actor;
DROP ROLE IF EXISTS dropoperator_01293_actor;
