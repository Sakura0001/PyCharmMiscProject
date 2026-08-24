-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_4 (database) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_4
-- factor expected_status=success
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS dcl_01400_grantee;
DROP ROLE IF EXISTS dcl_01400_grantor;
DROP ROLE IF EXISTS dcl_01400_member;
CREATE ROLE dcl_01400_grantee;
CREATE ROLE dcl_01400_grantor;
CREATE ROLE dcl_01400_member;
BEGIN;
GRANT CONNECT ON DATABASE dcl_01400_database TO CURRENT_USER GRANTED BY CURRENT_USER;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP OWNED BY dcl_01400_grantee;
DROP OWNED BY dcl_01400_member;
DROP OWNED BY dcl_01400_grantor;
DROP ROLE IF EXISTS dcl_01400_member;
DROP ROLE IF EXISTS dcl_01400_grantor;
DROP ROLE IF EXISTS dcl_01400_grantee;
