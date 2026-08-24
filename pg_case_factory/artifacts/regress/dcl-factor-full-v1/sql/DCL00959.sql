-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_3 (sequence) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=success
-- factor privilege_scope=table_privilege
-- factor grantee_shape=session_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS "dcl_00959_Grantee";
DROP ROLE IF EXISTS dcl_00959_grantor;
DROP ROLE IF EXISTS dcl_00959_member;
CREATE ROLE "dcl_00959_Grantee";
CREATE ROLE dcl_00959_grantor;
CREATE ROLE dcl_00959_member;
DROP SEQUENCE IF EXISTS dcl_00959_sequence;
CREATE SEQUENCE dcl_00959_sequence;
GRANT USAGE ON SEQUENCE dcl_00959_sequence TO dcl_00959_grantor WITH GRANT OPTION;
BEGIN;
SET ROLE dcl_00959_grantor;
GRANT USAGE ON SEQUENCE dcl_00959_sequence TO SESSION_USER WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP SEQUENCE IF EXISTS dcl_00959_sequence;
DROP OWNED BY "dcl_00959_Grantee";
DROP OWNED BY dcl_00959_member;
DROP OWNED BY dcl_00959_grantor;
DROP ROLE IF EXISTS dcl_00959_member;
DROP ROLE IF EXISTS dcl_00959_grantor;
DROP ROLE IF EXISTS "dcl_00959_Grantee";
