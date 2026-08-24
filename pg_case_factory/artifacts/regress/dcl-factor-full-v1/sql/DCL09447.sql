-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_6 (foreign_data_wrapper) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=session_user
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_09447_Grantee";
DROP ROLE IF EXISTS dcl_09447_grantor;
DROP ROLE IF EXISTS dcl_09447_member;
CREATE ROLE "dcl_09447_Grantee";
CREATE ROLE dcl_09447_grantor;
CREATE ROLE dcl_09447_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09447_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09447_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09447_missing_object TO SESSION_USER;
SET ROLE "dcl_09447_Grantee";
REVOKE USAGE ON FOREIGN DATA WRAPPER dcl_09447_missing_object FROM SESSION_USER GRANTED BY dcl_09447_grantor RESTRICT;
RESET ROLE;
SELECT true AS fdw_privilege_statement_completed;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09447_fdw CASCADE;
DROP OWNED BY "dcl_09447_Grantee";
DROP OWNED BY dcl_09447_member;
DROP OWNED BY dcl_09447_grantor;
DROP ROLE IF EXISTS dcl_09447_member;
DROP ROLE IF EXISTS dcl_09447_grantor;
DROP ROLE IF EXISTS "dcl_09447_Grantee";
