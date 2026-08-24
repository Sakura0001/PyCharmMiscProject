-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg_case_factory
-- create at    : 2026-08-20
-- version      : 1.0.0
-- description  : ALTER OPERATOR CLASS branch_rename=bounded_cross_branch_rename_effect_query_reset_state
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATORCLASS07375
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/alter_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/alter_operator_class.yaml
-- primary_obligation_id: AOC-EXT|07375|rename|effect_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 预清理本编号对象。
DROP SCHEMA IF EXISTS alteroperatorclass_07375_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperatorclass_07375_sch;
CREATE SCHEMA IF NOT EXISTS alteroperatorclass_07375_target_sch;
\set ON_ERROR_STOP off
-- primary-target-begin
ALTER OPERATOR CLASS alteroperatorclass_07375_sch.alteroperatorclass_07375_opc USING btree RENAME TO alteroperatorclass_07375_new_opc;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=42704
-- 4. 断言与目录审计。
SELECT count(*) AS opc_renamed FROM pg_catalog.pg_opclass WHERE opcname = 'alteroperatorclass_07375_new_opc' AND opcmethod = (SELECT oid FROM pg_catalog.pg_am WHERE amname = 'btree') ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS alteroperatorclass_07375_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperatorclass_07375_target_sch CASCADE;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_07375_sch.alteroperatorclass_07375_opc USING btree;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_07375_new_opc USING btree;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_07375_conflict_opc USING btree;
