-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_3 (sequence) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=current_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_07848_Grantee";
DROP ROLE IF EXISTS dcl_07848_grantor;
DROP ROLE IF EXISTS dcl_07848_member;
CREATE ROLE "dcl_07848_Grantee";
CREATE ROLE dcl_07848_grantor;
CREATE ROLE dcl_07848_member;
DROP SEQUENCE IF EXISTS dcl_07848_sequence;
CREATE SEQUENCE dcl_07848_sequence;
GRANT USAGE ON SEQUENCE dcl_07848_missing_object TO CURRENT_USER;
SET ROLE "dcl_07848_Grantee";
REVOKE GRANT OPTION FOR USAGE ON SEQUENCE dcl_07848_missing_object FROM CURRENT_USER GRANTED BY dcl_07848_grantor RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
DROP SEQUENCE IF EXISTS dcl_07848_sequence;
DROP OWNED BY "dcl_07848_Grantee";
DROP OWNED BY dcl_07848_member;
DROP OWNED BY dcl_07848_grantor;
DROP ROLE IF EXISTS dcl_07848_member;
DROP ROLE IF EXISTS dcl_07848_grantor;
DROP ROLE IF EXISTS "dcl_07848_Grantee";
