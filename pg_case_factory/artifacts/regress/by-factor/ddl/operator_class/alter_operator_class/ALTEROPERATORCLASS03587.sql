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
-- case_id: ALTEROPERATORCLASS03587
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/alter_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/alter_operator_class.yaml
-- primary_obligation_id: AOC-EXT|03587|owner_change|catalog_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 预清理本编号对象。
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperatorclass_03587_sch;
CREATE SCHEMA IF NOT EXISTS alteroperatorclass_03587_target_sch;
CREATE ROLE alteroperatorclass_03587_actor LOGIN;
GRANT USAGE ON SCHEMA alteroperatorclass_03587_sch TO alteroperatorclass_03587_actor;
CREATE OPERATOR CLASS alteroperatorclass_03587_sch.alteroperatorclass_03587_opc FOR TYPE integer USING hash AS STORAGE integer;
SET ROLE alteroperatorclass_03587_actor;
\set ON_ERROR_STOP off
-- primary-target-begin
ALTER OPERATOR CLASS alteroperatorclass_03587_sch.alteroperatorclass_03587_opc USING hash OWNER TO CURRENT_ROLE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=42501
-- 4. 断言与目录审计。
SELECT count(*) AS opc_owner_changed FROM pg_catalog.pg_opclass WHERE opcname = 'alteroperatorclass_03587_opc' AND opcmethod = (SELECT oid FROM pg_catalog.pg_am WHERE amname = 'hash') AND opcowner = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = current_role) ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS alteroperatorclass_03587_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperatorclass_03587_target_sch CASCADE;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_03587_sch.alteroperatorclass_03587_opc USING hash;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_03587_new_opc USING hash;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_03587_conflict_opc USING hash;
DROP OWNED BY alteroperatorclass_03587_actor;
DROP ROLE IF EXISTS alteroperatorclass_03587_actor;
