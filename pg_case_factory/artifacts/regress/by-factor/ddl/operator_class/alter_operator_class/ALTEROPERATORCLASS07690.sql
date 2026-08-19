-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg_case_factory
-- create at    : 2026-08-20
-- version      : 1.0.0
-- description  : ALTER OPERATOR CLASS branch_rename=bounded_cross_branch_rename_catalog_query_drop_objects
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATORCLASS07690
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/alter_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/alter_operator_class.yaml
-- primary_obligation_id: AOC-EXT|07690|rename|catalog_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 预清理本编号对象。
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperatorclass_07690_sch;
CREATE SCHEMA IF NOT EXISTS alteroperatorclass_07690_target_sch;
CREATE ROLE alteroperatorclass_07690_actor LOGIN;
GRANT USAGE ON SCHEMA alteroperatorclass_07690_sch TO alteroperatorclass_07690_actor;
CREATE OPERATOR CLASS alteroperatorclass_07690_sch.alteroperatorclass_07690_opc FOR TYPE integer USING hash AS STORAGE integer;
SET ROLE alteroperatorclass_07690_actor;
\set ON_ERROR_STOP off
-- primary-target-begin
ALTER OPERATOR CLASS alteroperatorclass_07690_sch.alteroperatorclass_07690_opc USING hash RENAME TO alteroperatorclass_07690_new_opc;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=42501
-- 4. 断言与目录审计。
SELECT count(*) AS opc_renamed FROM pg_catalog.pg_opclass WHERE opcname = 'alteroperatorclass_07690_new_opc' AND opcmethod = (SELECT oid FROM pg_catalog.pg_am WHERE amname = 'hash') ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS alteroperatorclass_07690_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperatorclass_07690_target_sch CASCADE;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_07690_sch.alteroperatorclass_07690_opc USING hash;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_07690_new_opc USING hash;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_07690_conflict_opc USING hash;
DROP OWNED BY alteroperatorclass_07690_actor;
DROP ROLE IF EXISTS alteroperatorclass_07690_actor;
