-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_3 (sequence) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS "dcl_08076_Grantee";
DROP ROLE IF EXISTS dcl_08076_grantor;
DROP ROLE IF EXISTS dcl_08076_member;
CREATE ROLE "dcl_08076_Grantee";
CREATE ROLE dcl_08076_grantor;
CREATE ROLE dcl_08076_member;
DROP SEQUENCE IF EXISTS dcl_08076_sequence;
CREATE SEQUENCE dcl_08076_sequence;
GRANT USAGE ON SEQUENCE dcl_08076_missing_object TO CURRENT_ROLE;
SET ROLE "dcl_08076_Grantee";
REVOKE GRANT OPTION FOR USAGE ON SEQUENCE dcl_08076_missing_object FROM CURRENT_ROLE GRANTED BY dcl_08076_grantor RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
DROP SEQUENCE IF EXISTS dcl_08076_sequence;
DROP OWNED BY "dcl_08076_Grantee";
DROP OWNED BY dcl_08076_member;
DROP OWNED BY dcl_08076_grantor;
DROP ROLE IF EXISTS dcl_08076_member;
DROP ROLE IF EXISTS dcl_08076_grantor;
DROP ROLE IF EXISTS "dcl_08076_Grantee";
