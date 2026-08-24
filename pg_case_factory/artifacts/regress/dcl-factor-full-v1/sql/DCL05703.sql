-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_13 (tablespace) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS "dcl_05703_Grantee";
DROP ROLE IF EXISTS dcl_05703_grantor;
DROP ROLE IF EXISTS dcl_05703_member;
CREATE ROLE "dcl_05703_Grantee";
CREATE ROLE dcl_05703_grantor;
CREATE ROLE dcl_05703_member;
SET ROLE "dcl_05703_Grantee";
GRANT CREATE ON TABLESPACE dcl_05703_missing_object TO "dcl_05703_Grantee" GRANTED BY dcl_05703_grantor;
RESET ROLE;
SELECT has_tablespace_privilege(CURRENT_USER, 'dcl_05703_tablespace', 'CREATE');
DROP OWNED BY "dcl_05703_Grantee";
DROP OWNED BY dcl_05703_member;
DROP OWNED BY dcl_05703_grantor;
DROP ROLE IF EXISTS dcl_05703_member;
DROP ROLE IF EXISTS dcl_05703_grantor;
DROP ROLE IF EXISTS "dcl_05703_Grantee";
