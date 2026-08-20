-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE OPERATOR FAMILY invalid_combination=syntax_valid_semantic_error
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEOPERATORFAMILY00580
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_family/create_operator_family.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_family/create_operator_family.yaml
-- primary_obligation_id: COF-EXT|00580|effect_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR FAMILY IF EXISTS "createoperatorfamily_00580_QOpfam" CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE OPERATOR FAMILY。
-- primary-target-begin
CREATE OPERATOR FAMILY "createoperatorfamily_00580_QOpfam" USING pgcf_nosucham;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS opfamily_effect FROM pg_catalog.pg_opfamily opf JOIN pg_catalog.pg_am am ON opf.opfmethod = am.oid WHERE opf.opfname = 'createoperatorfamily_00580_QOpfam' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP OPERATOR FAMILY IF EXISTS "createoperatorfamily_00580_QOpfam" CASCADE;
