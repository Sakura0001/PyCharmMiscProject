-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_3 (sequence) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=success
-- factor privilege_scope=table_privilege
-- factor grantee_shape=session_user
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
DROP ROLE IF EXISTS dcl_07742_grantee;
DROP ROLE IF EXISTS dcl_07742_grantor;
DROP ROLE IF EXISTS dcl_07742_member;
CREATE ROLE dcl_07742_grantee;
CREATE ROLE dcl_07742_grantor;
CREATE ROLE dcl_07742_member;
DROP SEQUENCE IF EXISTS dcl_07742_sequence;
CREATE SEQUENCE dcl_07742_sequence;
GRANT USAGE ON SEQUENCE dcl_07742_sequence TO SESSION_USER;
BEGIN;
REVOKE USAGE ON SEQUENCE dcl_07742_sequence FROM SESSION_USER GRANTED BY CURRENT_USER RESTRICT;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP SEQUENCE IF EXISTS dcl_07742_sequence;
DROP OWNED BY dcl_07742_grantee;
DROP OWNED BY dcl_07742_member;
DROP OWNED BY dcl_07742_grantor;
DROP ROLE IF EXISTS dcl_07742_member;
DROP ROLE IF EXISTS dcl_07742_grantor;
DROP ROLE IF EXISTS dcl_07742_grantee;
