-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_10 (large_object) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_10
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS "dcl_04125_Grantee";
DROP ROLE IF EXISTS dcl_04125_grantor;
DROP ROLE IF EXISTS dcl_04125_member;
CREATE ROLE "dcl_04125_Grantee";
CREATE ROLE dcl_04125_grantor;
CREATE ROLE dcl_04125_member;
SELECT pg_catalog.lo_unlink(1800000000 + 10) WHERE pg_catalog.lo_open(1800000000 + 10, 131072) IS NOT NULL;
SET ROLE "dcl_04125_Grantee";
GRANT SELECT ON LARGE OBJECT 1800000010 TO PUBLIC GRANTED BY dcl_04125_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'table_privilege' AS privilege_scope;
SELECT pg_catalog.lo_unlink(1800000010);
DROP OWNED BY "dcl_04125_Grantee";
DROP OWNED BY dcl_04125_member;
DROP OWNED BY dcl_04125_grantor;
DROP ROLE IF EXISTS dcl_04125_member;
DROP ROLE IF EXISTS dcl_04125_grantor;
DROP ROLE IF EXISTS "dcl_04125_Grantee";
