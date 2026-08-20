-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP OPERATOR operand_data_type=text
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPOPERATOR00025
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator/drop_operator.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator/drop_operator.yaml
-- primary_obligation_id: DROPOPERATOR-SFV|sfv-c39464c42def6b80accac401|drop_operator
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR IF EXISTS dropoperator_00025_op (text, text) CASCADE;
DROP FUNCTION IF EXISTS dropoperator_00025_opfn;
\set ON_ERROR_STOP on
-- 2. 创建完整本地 operator 和因子专用夹具。
CREATE FUNCTION dropoperator_00025_opfn(text, text) RETURNS text AS $$ SELECT $1; $$ LANGUAGE immutable;
CREATE OPERATOR dropoperator_00025_op (PROCEDURE = dropoperator_00025_opfn, LEFTARG = text, RIGHTARG = text);
-- 3. 执行唯一获得覆盖信用的 DROP OPERATOR。
-- primary-target-begin
DROP OPERATOR dropoperator_00025_op (text, text);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS operator_absent FROM pg_catalog.pg_operator WHERE oprname = 'dropoperator_00025_op' AND oprleft = 'text'::regtype AND oprright = 'text'::regtype ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP OPERATOR IF EXISTS dropoperator_00025_op (text, text) CASCADE;
DROP FUNCTION IF EXISTS dropoperator_00025_opfn;
