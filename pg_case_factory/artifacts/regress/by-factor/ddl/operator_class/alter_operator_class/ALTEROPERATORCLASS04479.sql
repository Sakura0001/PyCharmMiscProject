-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg_case_factory
-- create at    : 2026-08-20
-- version      : 1.0.0
-- description  : ALTER OPERATOR CLASS branch_owner=bounded_cross_branch_owner_error_assertion_reset_state
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATORCLASS04479
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/alter_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/alter_operator_class.yaml
-- primary_obligation_id: AOC-EXT|04479|owner_change|error_assertion|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 预清理本编号对象。
DROP SCHEMA IF EXISTS alteroperatorclass_04479_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperatorclass_04479_sch;
CREATE SCHEMA IF NOT EXISTS alteroperatorclass_04479_target_sch;
CREATE OPERATOR CLASS alteroperatorclass_04479_sch.alteroperatorclass_04479_opc FOR TYPE integer USING spgist AS STORAGE integer;
\set ON_ERROR_STOP off
-- primary-target-begin
ALTER OPERATOR CLASS alteroperatorclass_04479_sch.alteroperatorclass_04479_opc USING spgist OWNER TO alteroperatorclass_04479_nonexistent_role;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=42704
-- 4. 断言与目录审计。
SELECT count(*) AS opc_present FROM pg_catalog.pg_opclass WHERE opcname = 'alteroperatorclass_04479_opc' AND opcmethod = (SELECT oid FROM pg_catalog.pg_am WHERE amname = 'spgist') ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS alteroperatorclass_04479_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperatorclass_04479_target_sch CASCADE;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_04479_sch.alteroperatorclass_04479_opc USING spgist;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_04479_new_opc USING spgist;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_04479_conflict_opc USING spgist;
