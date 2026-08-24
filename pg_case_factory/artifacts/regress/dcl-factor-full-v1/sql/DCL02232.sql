-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_5 (domain) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=role_name
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_02232_Grantee";
DROP ROLE IF EXISTS dcl_02232_grantor;
DROP ROLE IF EXISTS dcl_02232_member;
CREATE ROLE "dcl_02232_Grantee";
CREATE ROLE dcl_02232_grantor;
CREATE ROLE dcl_02232_member;
DROP DOMAIN IF EXISTS dcl_02232_domain;
CREATE DOMAIN dcl_02232_domain AS text;
SET ROLE "dcl_02232_Grantee";
GRANT USAGE ON DOMAIN dcl_02232_missing_object TO "dcl_02232_Grantee" WITH INHERIT TRUE GRANTED BY dcl_02232_grantor;
RESET ROLE;
SELECT true AS privilege_effect_observed;
DROP DOMAIN IF EXISTS dcl_02232_domain;
DROP OWNED BY "dcl_02232_Grantee";
DROP OWNED BY dcl_02232_member;
DROP OWNED BY dcl_02232_grantor;
DROP ROLE IF EXISTS dcl_02232_member;
DROP ROLE IF EXISTS dcl_02232_grantor;
DROP ROLE IF EXISTS "dcl_02232_Grantee";
