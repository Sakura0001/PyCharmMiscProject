-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_3 (sequence) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=public
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_01041_Grantee";
DROP ROLE IF EXISTS dcl_01041_grantor;
DROP ROLE IF EXISTS dcl_01041_member;
CREATE ROLE "dcl_01041_Grantee";
CREATE ROLE dcl_01041_grantor;
CREATE ROLE dcl_01041_member;
DROP SEQUENCE IF EXISTS dcl_01041_sequence;
CREATE SEQUENCE dcl_01041_sequence;
SET ROLE "dcl_01041_Grantee";
GRANT USAGE ON SEQUENCE dcl_01041_missing_object TO PUBLIC WITH ADMIN OPTION GRANTED BY dcl_01041_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'column_privilege' AS privilege_scope;
DROP SEQUENCE IF EXISTS dcl_01041_sequence;
DROP OWNED BY "dcl_01041_Grantee";
DROP OWNED BY dcl_01041_member;
DROP OWNED BY dcl_01041_grantor;
DROP ROLE IF EXISTS dcl_01041_member;
DROP ROLE IF EXISTS dcl_01041_grantor;
DROP ROLE IF EXISTS "dcl_01041_Grantee";
