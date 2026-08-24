-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_10 (large_object) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_10
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=public
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_04187_grantee;
DROP ROLE IF EXISTS dcl_04187_grantor;
DROP ROLE IF EXISTS dcl_04187_member;
CREATE ROLE dcl_04187_grantee;
CREATE ROLE dcl_04187_grantor;
CREATE ROLE dcl_04187_member;
SELECT pg_catalog.lo_unlink(1800000000 + 10) WHERE pg_catalog.lo_open(1800000000 + 10, 131072) IS NOT NULL;
BEGIN;
SET ROLE dcl_04187_grantee;
GRANT SELECT ON LARGE OBJECT 1800000010 TO PUBLIC WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT true AS large_object_privilege_statement_completed;
ROLLBACK;
SELECT pg_catalog.lo_unlink(1800000010);
DROP OWNED BY dcl_04187_grantee;
DROP OWNED BY dcl_04187_member;
DROP OWNED BY dcl_04187_grantor;
DROP ROLE IF EXISTS dcl_04187_member;
DROP ROLE IF EXISTS dcl_04187_grantor;
DROP ROLE IF EXISTS dcl_04187_grantee;
