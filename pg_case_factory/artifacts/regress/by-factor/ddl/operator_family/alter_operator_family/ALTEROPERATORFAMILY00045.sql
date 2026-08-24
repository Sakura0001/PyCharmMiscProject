-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg_case_factory
-- create at    : 2026-08-20
-- version      : 1.0.0
-- description  : ALTER OPERATOR FAMILY privilege_context=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATORFAMILY00045
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_family/alter_operator_family.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_family/alter_operator_family.yaml
-- primary_obligation_id: AOF-SFV|sfv-84790a8415b670803086cf16|add_elements
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 预清理本编号对象。
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperatorfamily_00045_sch;
CREATE SCHEMA IF NOT EXISTS alteroperatorfamily_00045_target_sch;
CREATE ROLE alteroperatorfamily_00045_actor LOGIN;
GRANT USAGE ON SCHEMA alteroperatorfamily_00045_sch TO alteroperatorfamily_00045_actor;
CREATE OPERATOR FAMILY alteroperatorfamily_00045_opf USING btree;
SET ROLE alteroperatorfamily_00045_actor;
\set ON_ERROR_STOP off
-- primary-target-begin
ALTER OPERATOR FAMILY alteroperatorfamily_00045_opf USING btree ADD OPERATOR 1 =(integer, integer) FOR SEARCH;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=42501
-- 4. 断言与目录审计。
SELECT count(*) AS opf_present FROM pg_catalog.pg_opfamily WHERE opfname = 'alteroperatorfamily_00045_opf' AND opfmethod = (SELECT oid FROM pg_catalog.pg_am WHERE amname = 'btree') ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
RESET ROLE;
DO $$ DECLARE r record; BEGIN
  FOR r IN SELECT n.nspname, o.opfname, a.amname
    FROM pg_catalog.pg_opfamily o
    JOIN pg_catalog.pg_namespace n ON o.opfnamespace = n.oid
    JOIN pg_catalog.pg_am a ON o.opfmethod = a.oid
    WHERE o.opfname LIKE 'alteroperatorfamily_00045_%'
  LOOP
    EXECUTE format('DROP OPERATOR FAMILY IF EXISTS %I.%I USING %s CASCADE', r.nspname, r.opfname, r.amname);
  END LOOP;
END $$;
DROP SCHEMA IF EXISTS alteroperatorfamily_00045_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperatorfamily_00045_target_sch CASCADE;
DROP OWNED BY alteroperatorfamily_00045_actor;
DROP ROLE IF EXISTS alteroperatorfamily_00045_actor;
