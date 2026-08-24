-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_9 (language) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_9
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_role
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_03815_grantee;
DROP ROLE IF EXISTS dcl_03815_grantor;
DROP ROLE IF EXISTS dcl_03815_member;
CREATE ROLE dcl_03815_grantee;
CREATE ROLE dcl_03815_grantor;
CREATE ROLE dcl_03815_member;
BEGIN;
SET ROLE dcl_03815_grantee;
GRANT USAGE ON LANGUAGE plpgsql TO CURRENT_ROLE WITH INHERIT TRUE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT has_language_privilege(CURRENT_USER, 'plpgsql', 'USAGE');
ROLLBACK;
DROP OWNED BY dcl_03815_grantee;
DROP OWNED BY dcl_03815_member;
DROP OWNED BY dcl_03815_grantor;
DROP ROLE IF EXISTS dcl_03815_member;
DROP ROLE IF EXISTS dcl_03815_grantor;
DROP ROLE IF EXISTS dcl_03815_grantee;
