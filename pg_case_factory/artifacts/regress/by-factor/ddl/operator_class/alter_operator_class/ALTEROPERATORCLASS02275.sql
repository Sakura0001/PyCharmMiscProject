-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg_case_factory
-- create at    : 2026-08-20
-- version      : 1.0.0
-- description  : ALTER OPERATOR CLASS branch_owner=bounded_cross_branch_owner_effect_query_reset_state
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATORCLASS02275
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/alter_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/alter_operator_class.yaml
-- primary_obligation_id: AOC-EXT|02275|owner_change|effect_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 预清理本编号对象。
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperatorclass_02275_sch;
CREATE SCHEMA IF NOT EXISTS alteroperatorclass_02275_target_sch;
CREATE ROLE alteroperatorclass_02275_actor LOGIN;
GRANT USAGE ON SCHEMA alteroperatorclass_02275_sch TO alteroperatorclass_02275_actor;
SET ROLE alteroperatorclass_02275_actor;
\set ON_ERROR_STOP off
-- primary-target-begin
ALTER OPERATOR CLASS alteroperatorclass_02275_sch.alteroperatorclass_02275_opc USING gin OWNER TO SESSION_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=42704
-- 4. 断言与目录审计。
SELECT count(*) AS opc_owner_changed FROM pg_catalog.pg_opclass WHERE opcname = 'alteroperatorclass_02275_opc' AND opcmethod = (SELECT oid FROM pg_catalog.pg_am WHERE amname = 'gin') AND opcowner = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = session_user) ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS alteroperatorclass_02275_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperatorclass_02275_target_sch CASCADE;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_02275_sch.alteroperatorclass_02275_opc USING gin;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_02275_new_opc USING gin;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_02275_conflict_opc USING gin;
DROP OWNED BY alteroperatorclass_02275_actor;
DROP ROLE IF EXISTS alteroperatorclass_02275_actor;
