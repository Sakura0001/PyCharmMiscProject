-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_10 (large_object) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_10
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS "dcl_11061_Grantee";
DROP ROLE IF EXISTS dcl_11061_grantor;
DROP ROLE IF EXISTS dcl_11061_member;
CREATE ROLE "dcl_11061_Grantee";
CREATE ROLE dcl_11061_grantor;
CREATE ROLE dcl_11061_member;
SELECT pg_catalog.lo_unlink(1800000000 + 10) WHERE pg_catalog.lo_open(1800000000 + 10, 131072) IS NOT NULL;
GRANT SELECT ON LARGE OBJECT 1800000010 TO CURRENT_USER;
SET ROLE "dcl_11061_Grantee";
REVOKE ADMIN OPTION FOR SELECT ON LARGE OBJECT 1800000010 FROM CURRENT_USER GRANTED BY dcl_11061_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
SELECT pg_catalog.lo_unlink(1800000010);
DROP OWNED BY "dcl_11061_Grantee";
DROP OWNED BY dcl_11061_member;
DROP OWNED BY dcl_11061_grantor;
DROP ROLE IF EXISTS dcl_11061_member;
DROP ROLE IF EXISTS dcl_11061_grantor;
DROP ROLE IF EXISTS "dcl_11061_Grantee";
