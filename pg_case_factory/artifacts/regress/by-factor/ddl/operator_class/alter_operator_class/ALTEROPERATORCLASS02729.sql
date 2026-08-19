-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg_case_factory
-- create at    : 2026-08-20
-- version      : 1.0.0
-- description  : ALTER OPERATOR CLASS branch_owner=bounded_cross_branch_owner_catalog_query_reset_state
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATORCLASS02729
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/alter_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/alter_operator_class.yaml
-- primary_obligation_id: AOC-EXT|02729|owner_change|catalog_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 预清理本编号对象。
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperatorclass_02729_sch;
CREATE SCHEMA IF NOT EXISTS alteroperatorclass_02729_target_sch;
CREATE ROLE alteroperatorclass_02729_new_owner LOGIN;
CREATE ROLE alteroperatorclass_02729_actor LOGIN;
GRANT USAGE ON SCHEMA alteroperatorclass_02729_sch TO alteroperatorclass_02729_actor;
CREATE OPERATOR CLASS "alteroperatorclass_02729_opc" FOR TYPE integer USING gist AS STORAGE integer;
SET ROLE alteroperatorclass_02729_actor;
\set ON_ERROR_STOP off
-- primary-target-begin
ALTER OPERATOR CLASS "alteroperatorclass_02729_opc" USING gist OWNER TO alteroperatorclass_02729_new_owner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=42501
-- 4. 断言与目录审计。
SELECT count(*) AS opc_owner_changed FROM pg_catalog.pg_opclass WHERE opcname = 'alteroperatorclass_02729_opc' AND opcmethod = (SELECT oid FROM pg_catalog.pg_am WHERE amname = 'gist') AND opcowner = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'alteroperatorclass_02729_new_owner') ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS alteroperatorclass_02729_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperatorclass_02729_target_sch CASCADE;
DROP OPERATOR CLASS IF EXISTS "alteroperatorclass_02729_opc" USING gist;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_02729_new_opc USING gist;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_02729_conflict_opc USING gist;
DROP ROLE IF EXISTS alteroperatorclass_02729_new_owner;
DROP OWNED BY alteroperatorclass_02729_actor;
DROP ROLE IF EXISTS alteroperatorclass_02729_actor;
