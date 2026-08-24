-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg_case_factory
-- create at    : 2026-08-20
-- version      : 1.0.0
-- description  : ALTER OPERATOR FAMILY branch_set_schema=bounded_cross_branch_set_schema_effect_query_reset_state
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATORFAMILY04395
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_family/alter_operator_family.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_family/alter_operator_family.yaml
-- primary_obligation_id: AOF-EXT|04395|set_schema|effect_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 预清理本编号对象。
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperatorfamily_04395_sch;
CREATE SCHEMA IF NOT EXISTS alteroperatorfamily_04395_target_sch;
CREATE ROLE alteroperatorfamily_04395_actor LOGIN;
GRANT USAGE ON SCHEMA alteroperatorfamily_04395_sch TO alteroperatorfamily_04395_actor;
CREATE OPERATOR FAMILY "alteroperatorfamily_04395_opf" USING btree;
SET ROLE alteroperatorfamily_04395_actor;
\set ON_ERROR_STOP off
-- primary-target-begin
ALTER OPERATOR FAMILY "alteroperatorfamily_04395_opf" USING btree SET SCHEMA alteroperatorfamily_04395_target_sch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=42501
-- 4. 断言与目录审计。
SELECT count(*) AS opf_schema_changed FROM pg_catalog.pg_opfamily WHERE opfname = 'alteroperatorfamily_04395_opf' AND opfmethod = (SELECT oid FROM pg_catalog.pg_am WHERE amname = 'btree') AND opfnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'alteroperatorfamily_04395_target_sch') ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
RESET ROLE;
DO $$ DECLARE r record; BEGIN
  FOR r IN SELECT n.nspname, o.opfname, a.amname
    FROM pg_catalog.pg_opfamily o
    JOIN pg_catalog.pg_namespace n ON o.opfnamespace = n.oid
    JOIN pg_catalog.pg_am a ON o.opfmethod = a.oid
    WHERE o.opfname LIKE 'alteroperatorfamily_04395_%'
  LOOP
    EXECUTE format('DROP OPERATOR FAMILY IF EXISTS %I.%I USING %s CASCADE', r.nspname, r.opfname, r.amname);
  END LOOP;
END $$;
DROP SCHEMA IF EXISTS alteroperatorfamily_04395_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperatorfamily_04395_target_sch CASCADE;
DROP OWNED BY alteroperatorfamily_04395_actor;
DROP ROLE IF EXISTS alteroperatorfamily_04395_actor;
