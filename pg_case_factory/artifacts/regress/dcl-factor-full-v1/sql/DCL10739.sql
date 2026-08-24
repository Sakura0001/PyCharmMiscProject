-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_9 (language) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_9
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=session_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_10739_grantee;
DROP ROLE IF EXISTS dcl_10739_grantor;
DROP ROLE IF EXISTS dcl_10739_member;
CREATE ROLE dcl_10739_grantee;
CREATE ROLE dcl_10739_grantor;
CREATE ROLE dcl_10739_member;
GRANT USAGE ON LANGUAGE plpgsql TO SESSION_USER;
BEGIN;
SET ROLE dcl_10739_grantee;
REVOKE GRANT OPTION FOR USAGE ON LANGUAGE plpgsql FROM SESSION_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT has_language_privilege(CURRENT_USER, 'plpgsql', 'USAGE');
ROLLBACK;
DROP OWNED BY dcl_10739_grantee;
DROP OWNED BY dcl_10739_member;
DROP OWNED BY dcl_10739_grantor;
DROP ROLE IF EXISTS dcl_10739_member;
DROP ROLE IF EXISTS dcl_10739_grantor;
DROP ROLE IF EXISTS dcl_10739_grantee;
