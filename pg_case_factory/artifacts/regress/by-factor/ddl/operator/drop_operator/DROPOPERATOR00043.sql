-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP OPERATOR transaction_outcome=rollback
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPOPERATOR00043
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator/drop_operator.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator/drop_operator.yaml
-- primary_obligation_id: DROPOPERATOR-RISK|transaction|rollback
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR IF EXISTS dropoperator_00043_op (integer, integer) CASCADE;
DROP FUNCTION IF EXISTS dropoperator_00043_opfn;
\set ON_ERROR_STOP on
-- 2. 创建完整本地 operator 和因子专用夹具。
CREATE FUNCTION dropoperator_00043_opfn(integer, integer) RETURNS integer AS $$ SELECT $1; $$ LANGUAGE immutable;
CREATE OPERATOR dropoperator_00043_op (PROCEDURE = dropoperator_00043_opfn, LEFTARG = integer, RIGHTARG = integer);
BEGIN;
-- 3. 执行唯一获得覆盖信用的 DROP OPERATOR。
-- primary-target-begin
DROP OPERATOR dropoperator_00043_op (integer, integer);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
ROLLBACK;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS operator_present FROM pg_catalog.pg_operator WHERE oprname = 'dropoperator_00043_op' AND oprleft = 'integer'::regtype AND oprright = 'integer'::regtype ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP OPERATOR IF EXISTS dropoperator_00043_op (integer, integer) CASCADE;
DROP FUNCTION IF EXISTS dropoperator_00043_opfn;
