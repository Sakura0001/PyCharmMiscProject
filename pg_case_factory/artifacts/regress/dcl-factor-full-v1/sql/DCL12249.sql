-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_13 (tablespace) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_12249_Grantee";
DROP ROLE IF EXISTS dcl_12249_grantor;
DROP ROLE IF EXISTS dcl_12249_member;
CREATE ROLE "dcl_12249_Grantee";
CREATE ROLE dcl_12249_grantor;
CREATE ROLE dcl_12249_member;
GRANT CREATE ON TABLESPACE dcl_12249_missing_object TO "dcl_12249_Grantee";
SET ROLE "dcl_12249_Grantee";
REVOKE CREATE ON TABLESPACE dcl_12249_missing_object FROM "dcl_12249_Grantee" GRANTED BY dcl_12249_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'table_privilege' AS privilege_scope;
DROP OWNED BY "dcl_12249_Grantee";
DROP OWNED BY dcl_12249_member;
DROP OWNED BY dcl_12249_grantor;
DROP ROLE IF EXISTS dcl_12249_member;
DROP ROLE IF EXISTS dcl_12249_grantor;
DROP ROLE IF EXISTS "dcl_12249_Grantee";
