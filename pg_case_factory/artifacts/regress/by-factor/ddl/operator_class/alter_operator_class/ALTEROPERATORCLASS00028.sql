-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg_case_factory
-- create at    : 2026-08-20
-- version      : 1.0.0
-- description  : ALTER OPERATOR CLASS new_owner_shape=plain_role
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATORCLASS00028
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/alter_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/alter_operator_class.yaml
-- primary_obligation_id: AOC-SFV|sfv-47326fc5b6aea8e05429cf95|owner_change
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 预清理本编号对象。
DROP SCHEMA IF EXISTS alteroperatorclass_00028_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperatorclass_00028_sch;
CREATE SCHEMA IF NOT EXISTS alteroperatorclass_00028_target_sch;
CREATE ROLE alteroperatorclass_00028_new_owner LOGIN;
CREATE OPERATOR CLASS alteroperatorclass_00028_opc FOR TYPE integer USING btree AS STORAGE integer;
-- primary-target-begin
ALTER OPERATOR CLASS alteroperatorclass_00028_opc USING btree OWNER TO alteroperatorclass_00028_new_owner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=00000
-- 4. 断言与目录审计。
SELECT count(*) AS opc_owner_changed FROM pg_catalog.pg_opclass WHERE opcname = 'alteroperatorclass_00028_opc' AND opcmethod = (SELECT oid FROM pg_catalog.pg_am WHERE amname = 'btree') AND opcowner = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'alteroperatorclass_00028_new_owner') ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS alteroperatorclass_00028_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperatorclass_00028_target_sch CASCADE;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_00028_opc USING btree;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_00028_new_opc USING btree;
DROP OPERATOR CLASS IF EXISTS alteroperatorclass_00028_conflict_opc USING btree;
DROP ROLE IF EXISTS alteroperatorclass_00028_new_owner;
