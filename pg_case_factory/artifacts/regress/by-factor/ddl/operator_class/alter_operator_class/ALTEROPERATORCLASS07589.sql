-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg_case_factory
-- create at    : 2026-08-20
-- version      : 1.0.0
-- description  : ALTER OPERATOR CLASS branch_rename=bounded_cross_branch_rename_catalog_query_reset_state
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATORCLASS07589
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/alter_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/alter_operator_class.yaml
-- primary_obligation_id: AOC-EXT|07589|rename|catalog_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 预清理本编号对象。
DROP SCHEMA IF EXISTS alteroperatorclass_07589_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperatorclass_07589_sch;
CREATE SCHEMA IF NOT EXISTS alteroperatorclass_07589_target_sch;
\set ON_ERROR_STOP off
-- primary-target-begin
ALTER OPERATOR CLASS alteroperatorclass_07589_sch.alteroperatorclass_07589_opc USING gist RENAME TO alteroperatorclass_07589_new_opc;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=42704
-- 4. 断言与目录审计。
SELECT count(*) AS opc_renamed FROM pg_catalog.pg_opclass WHERE opcname = 'alteroperatorclass_07589_new_opc' AND opcmethod = (SELECT oid FROM pg_catalog.pg_am WHERE amname = 'gist') ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS alteroperatorclass_07589_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperatorclass_07589_target_sch CASCADE;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_07589_sch.alteroperatorclass_07589_opc USING gist;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_07589_new_opc USING gist;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_07589_conflict_opc USING gist;
