-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_13 (tablespace) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
-- factor expected_status=success
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_role
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_05444_grantee;
DROP ROLE IF EXISTS dcl_05444_grantor;
DROP ROLE IF EXISTS dcl_05444_member;
CREATE ROLE dcl_05444_grantee;
CREATE ROLE dcl_05444_grantor;
CREATE ROLE dcl_05444_member;
BEGIN;
GRANT CREATE ON TABLESPACE dcl_05444_tablespace TO CURRENT_ROLE GRANTED BY CURRENT_USER;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP OWNED BY dcl_05444_grantee;
DROP OWNED BY dcl_05444_member;
DROP OWNED BY dcl_05444_grantor;
DROP ROLE IF EXISTS dcl_05444_member;
DROP ROLE IF EXISTS dcl_05444_grantor;
DROP ROLE IF EXISTS dcl_05444_grantee;
