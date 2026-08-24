-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg_case_factory
-- create at    : 2026-08-20
-- version      : 1.0.0
-- description  : ALTER OPERATOR CLASS branch_set_schema=bounded_cross_branch_set_schema_catalog_query_drop_objects
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATORCLASS08260
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/alter_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/alter_operator_class.yaml
-- primary_obligation_id: AOC-EXT|08260|set_schema|catalog_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 3F000
-- 1. 预清理本编号对象。
DROP SCHEMA IF EXISTS alteroperatorclass_08260_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperatorclass_08260_sch;
CREATE OPERATOR CLASS "alteroperatorclass_08260_opc" FOR TYPE integer USING btree AS STORAGE integer;
\set ON_ERROR_STOP off
-- primary-target-begin
ALTER OPERATOR CLASS "alteroperatorclass_08260_opc" USING btree SET SCHEMA alteroperatorclass_08260_target_sch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=3F000
-- 4. 断言与目录审计。
SELECT count(*) AS opc_schema_changed FROM pg_catalog.pg_opclass WHERE opcname = 'alteroperatorclass_08260_opc' AND opcmethod = (SELECT oid FROM pg_catalog.pg_am WHERE amname = 'btree') AND opcnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'alteroperatorclass_08260_target_sch') ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '3F000' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS alteroperatorclass_08260_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperatorclass_08260_target_sch CASCADE;
DROP OPERATOR CLASS IF EXISTS "alteroperatorclass_08260_opc" USING btree;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_08260_new_opc USING btree;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_08260_conflict_opc USING btree;
