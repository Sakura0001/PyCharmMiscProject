-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg_case_factory
-- create at    : 2026-08-20
-- version      : 1.0.0
-- description  : ALTER OPERATOR FAMILY branch_add=bounded_cross_branch_add_effect_query_reset_state
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTEROPERATORFAMILY00159
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_family/alter_operator_family.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_family/alter_operator_family.yaml
-- primary_obligation_id: AOF-EXT|00159|add_elements|effect_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42883
-- 1. 预清理本编号对象。
DO $$ DECLARE r record; BEGIN
  FOR r IN SELECT n.nspname, o.opfname, a.amname
    FROM pg_catalog.pg_opfamily o
    JOIN pg_catalog.pg_namespace n ON o.opfnamespace = n.oid
    JOIN pg_catalog.pg_am a ON o.opfmethod = a.oid
    WHERE o.opfname LIKE 'alteroperatorfamily_00159_%'
  LOOP
    EXECUTE format('DROP OPERATOR FAMILY IF EXISTS %I.%I USING %s CASCADE', r.nspname, r.opfname, r.amname);
  END LOOP;
END $$;
\set ON_ERROR_STOP on
-- 2. 构造本编号对象与角色。
CREATE SCHEMA IF NOT EXISTS alteroperatorfamily_00159_sch;
CREATE SCHEMA IF NOT EXISTS alteroperatorfamily_00159_target_sch;
DROP DOMAIN IF EXISTS alteroperatorfamily_00159_custype CASCADE; CREATE DOMAIN alteroperatorfamily_00159_custype AS integer;
CREATE OPERATOR FAMILY alteroperatorfamily_00159_opf USING btree;
\set ON_ERROR_STOP off
-- primary-target-begin
ALTER OPERATOR FAMILY alteroperatorfamily_00159_opf USING btree ADD FUNCTION 1 alteroperatorfamily_00159_missingfn(alteroperatorfamily_00159_custype, alteroperatorfamily_00159_custype);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=42883
-- 4. 断言与目录审计。
SELECT count(*) AS opf_present FROM pg_catalog.pg_opfamily WHERE opfname = 'alteroperatorfamily_00159_opf' AND opfmethod = (SELECT oid FROM pg_catalog.pg_am WHERE amname = 'btree') ORDER BY count(*) LIMIT 1;
SELECT :'target_sqlstate' = '42883' AS target_sqlstate_matches_expected;
\set ON_ERROR_STOP off
-- 5. 清理全部本编号对象。
DO $$ DECLARE r record; BEGIN
  FOR r IN SELECT n.nspname, o.opfname, a.amname
    FROM pg_catalog.pg_opfamily o
    JOIN pg_catalog.pg_namespace n ON o.opfnamespace = n.oid
    JOIN pg_catalog.pg_am a ON o.opfmethod = a.oid
    WHERE o.opfname LIKE 'alteroperatorfamily_00159_%'
  LOOP
    EXECUTE format('DROP OPERATOR FAMILY IF EXISTS %I.%I USING %s CASCADE', r.nspname, r.opfname, r.amname);
  END LOOP;
END $$;
DROP SCHEMA IF EXISTS alteroperatorfamily_00159_sch CASCADE;
DROP SCHEMA IF EXISTS alteroperatorfamily_00159_target_sch CASCADE;
DROP DOMAIN IF EXISTS alteroperatorfamily_00159_custype CASCADE;
