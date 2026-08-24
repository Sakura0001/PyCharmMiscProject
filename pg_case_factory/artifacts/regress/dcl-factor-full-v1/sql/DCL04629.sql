-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_11 (parameter) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_11
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS "dcl_04629_Grantee";
DROP ROLE IF EXISTS dcl_04629_grantor;
DROP ROLE IF EXISTS dcl_04629_member;
CREATE ROLE "dcl_04629_Grantee";
CREATE ROLE dcl_04629_grantor;
CREATE ROLE dcl_04629_member;
SET ROLE "dcl_04629_Grantee";
GRANT SELECT ON PARAMETER work_mem TO "dcl_04629_Grantee" WITH ADMIN OPTION GRANTED BY dcl_04629_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'column_privilege' AS privilege_scope;
DROP OWNED BY "dcl_04629_Grantee";
DROP OWNED BY dcl_04629_member;
DROP OWNED BY dcl_04629_grantor;
DROP ROLE IF EXISTS dcl_04629_member;
DROP ROLE IF EXISTS dcl_04629_grantor;
DROP ROLE IF EXISTS "dcl_04629_Grantee";
