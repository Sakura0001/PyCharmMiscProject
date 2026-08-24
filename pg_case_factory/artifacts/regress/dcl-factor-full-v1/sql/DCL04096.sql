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
-- factor expected_status=success
-- factor privilege_scope=table_privilege
-- factor grantee_shape=current_role
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_04096_grantee;
DROP ROLE IF EXISTS dcl_04096_grantor;
DROP ROLE IF EXISTS dcl_04096_member;
CREATE ROLE dcl_04096_grantee;
CREATE ROLE dcl_04096_grantor;
CREATE ROLE dcl_04096_member;
SELECT pg_catalog.lo_unlink(1800000000 + 10) WHERE pg_catalog.lo_open(1800000000 + 10, 131072) IS NOT NULL;
GRANT SELECT ON LARGE OBJECT 1800000010 TO CURRENT_ROLE WITH GRANT OPTION;
SELECT true AS large_object_privilege_statement_completed;
RESET ROLE;
RESET ALL;
SELECT pg_catalog.lo_unlink(1800000010);
DROP OWNED BY dcl_04096_grantee;
DROP OWNED BY dcl_04096_member;
DROP OWNED BY dcl_04096_grantor;
DROP ROLE IF EXISTS dcl_04096_member;
DROP ROLE IF EXISTS dcl_04096_grantor;
DROP ROLE IF EXISTS dcl_04096_grantee;
