-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_10 (large_object) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_10
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS "dcl_11163_Grantee";
DROP ROLE IF EXISTS dcl_11163_grantor;
DROP ROLE IF EXISTS dcl_11163_member;
CREATE ROLE "dcl_11163_Grantee";
CREATE ROLE dcl_11163_grantor;
CREATE ROLE dcl_11163_member;
SELECT pg_catalog.lo_unlink(1800000000 + 10) WHERE pg_catalog.lo_open(1800000000 + 10, 131072) IS NOT NULL;
GRANT SELECT ON LARGE OBJECT 1800000010 TO CURRENT_ROLE;
SET ROLE "dcl_11163_Grantee";
REVOKE SELECT ON LARGE OBJECT 1800000010 FROM CURRENT_ROLE GRANTED BY dcl_11163_grantor RESTRICT;
RESET ROLE;
SELECT true AS large_object_privilege_statement_completed;
SELECT pg_catalog.lo_unlink(1800000010);
DROP OWNED BY "dcl_11163_Grantee";
DROP OWNED BY dcl_11163_member;
DROP OWNED BY dcl_11163_grantor;
DROP ROLE IF EXISTS dcl_11163_member;
DROP ROLE IF EXISTS dcl_11163_grantor;
DROP ROLE IF EXISTS "dcl_11163_Grantee";
