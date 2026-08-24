-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP OPERATOR target_object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPOPERATOR01369
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator/drop_operator.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator/drop_operator.yaml
-- primary_obligation_id: DROPOPERATOR-EXT|01369|drop_operator|error_assertion|reset_state
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR IF EXISTS dropoperator_01369_op (integer, integer) CASCADE;
DROP FUNCTION IF EXISTS dropoperator_01369_opfn;
\set ON_ERROR_STOP on
-- 2. 创建完整本地 operator 和因子专用夹具。
CREATE FUNCTION dropoperator_01369_opfn(integer, integer) RETURNS integer AS $$ SELECT $1; $$ LANGUAGE immutable;
CREATE OPERATOR dropoperator_01369_op (PROCEDURE = dropoperator_01369_opfn, LEFTARG = integer, RIGHTARG = integer);
-- 3. 执行唯一获得覆盖信用的 DROP OPERATOR。
-- primary-target-begin
DROP OPERATOR IF EXISTS dropoperator_01369_op (integer, integer);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS operator_absent FROM pg_catalog.pg_operator WHERE oprname = 'dropoperator_01369_op' AND oprleft = 'integer'::regtype AND oprright = 'integer'::regtype ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP OPERATOR IF EXISTS dropoperator_01369_op (integer, integer) CASCADE;
DROP FUNCTION IF EXISTS dropoperator_01369_opfn;
