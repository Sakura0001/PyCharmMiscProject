-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg_case_factory
-- create at    : 2026-08-20
-- version      : 1.0.0
-- description  : ALTER OPERATOR FAMILY branch_owner=bounded_cross_branch_owner_catalog_query_drop_objects
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATORFAMILY03966
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_family/alter_operator_family.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_family/alter_operator_family.yaml
-- primary_obligation_id: AOF-EXT|03966|owner_change|catalog_query|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 预清理本编号对象。
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperatorfamily_03966_sch;
CREATE SCHEMA IF NOT EXISTS alteroperatorfamily_03966_target_sch;
CREATE ROLE alteroperatorfamily_03966_actor LOGIN;
GRANT USAGE ON SCHEMA alteroperatorfamily_03966_sch TO alteroperatorfamily_03966_actor;
CREATE OPERATOR FAMILY alteroperatorfamily_03966_opf USING btree;
SET ROLE alteroperatorfamily_03966_actor;
-- primary-target-begin
ALTER OPERATOR FAMILY alteroperatorfamily_03966_opf USING btree OWNER TO SESSION_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=00000
-- 4. 断言与目录审计。
SELECT count(*) AS opf_owner_changed FROM pg_catalog.pg_opfamily WHERE opfname = 'alteroperatorfamily_03966_opf' AND opfmethod = (SELECT oid FROM pg_catalog.pg_am WHERE amname = 'btree') AND opfowner = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = session_user) ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
RESET ROLE;
DO $$ DECLARE r record; BEGIN
  FOR r IN SELECT n.nspname, o.opfname, a.amname
    FROM pg_catalog.pg_opfamily o
    JOIN pg_catalog.pg_namespace n ON o.opfnamespace = n.oid
    JOIN pg_catalog.pg_am a ON o.opfmethod = a.oid
    WHERE o.opfname LIKE 'alteroperatorfamily_03966_%'
  LOOP
    EXECUTE format('DROP OPERATOR FAMILY IF EXISTS %I.%I USING %s CASCADE', r.nspname, r.opfname, r.amname);
  END LOOP;
END $$;
DROP SCHEMA IF EXISTS alteroperatorfamily_03966_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperatorfamily_03966_target_sch CASCADE;
DROP OWNED BY alteroperatorfamily_03966_actor;
DROP ROLE IF EXISTS alteroperatorfamily_03966_actor;
