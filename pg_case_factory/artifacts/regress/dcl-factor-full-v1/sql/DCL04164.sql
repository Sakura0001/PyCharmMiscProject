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
-- factor grantee_shape=session_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_04164_Grantee";
DROP ROLE IF EXISTS dcl_04164_grantor;
DROP ROLE IF EXISTS dcl_04164_member;
CREATE ROLE "dcl_04164_Grantee";
CREATE ROLE dcl_04164_grantor;
CREATE ROLE dcl_04164_member;
SELECT pg_catalog.lo_unlink(1800000000 + 10) WHERE pg_catalog.lo_open(1800000000 + 10, 131072) IS NOT NULL;
SET ROLE "dcl_04164_Grantee";
GRANT SELECT ON LARGE OBJECT 1800000010 TO SESSION_USER WITH GRANT OPTION GRANTED BY dcl_04164_grantor;
RESET ROLE;
SELECT true AS privilege_effect_observed;
SELECT pg_catalog.lo_unlink(1800000010);
DROP OWNED BY "dcl_04164_Grantee";
DROP OWNED BY dcl_04164_member;
DROP OWNED BY dcl_04164_grantor;
DROP ROLE IF EXISTS dcl_04164_member;
DROP ROLE IF EXISTS dcl_04164_grantor;
DROP ROLE IF EXISTS "dcl_04164_Grantee";
