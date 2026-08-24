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
-- factor grantee_shape=role_name
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS "dcl_04085_Grantee";
DROP ROLE IF EXISTS dcl_04085_grantor;
DROP ROLE IF EXISTS dcl_04085_member;
CREATE ROLE "dcl_04085_Grantee";
CREATE ROLE dcl_04085_grantor;
CREATE ROLE dcl_04085_member;
SELECT pg_catalog.lo_unlink(1800000000 + 10) WHERE pg_catalog.lo_open(1800000000 + 10, 131072) IS NOT NULL;
GRANT SELECT ON LARGE OBJECT 1800000010 TO dcl_04085_grantor WITH GRANT OPTION;
BEGIN;
SET ROLE dcl_04085_grantor;
GRANT SELECT ON LARGE OBJECT 1800000010 TO "dcl_04085_Grantee" WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
SELECT pg_catalog.lo_unlink(1800000010);
DROP OWNED BY "dcl_04085_Grantee";
DROP OWNED BY dcl_04085_member;
DROP OWNED BY dcl_04085_grantor;
DROP ROLE IF EXISTS dcl_04085_member;
DROP ROLE IF EXISTS dcl_04085_grantor;
DROP ROLE IF EXISTS "dcl_04085_Grantee";
