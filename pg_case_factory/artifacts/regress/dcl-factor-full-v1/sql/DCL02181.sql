-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_5 (domain) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS "dcl_02181_Grantee";
DROP ROLE IF EXISTS dcl_02181_grantor;
DROP ROLE IF EXISTS dcl_02181_member;
CREATE ROLE "dcl_02181_Grantee";
CREATE ROLE dcl_02181_grantor;
CREATE ROLE dcl_02181_member;
DROP DOMAIN IF EXISTS dcl_02181_domain;
CREATE DOMAIN dcl_02181_domain AS text;
SET ROLE "dcl_02181_Grantee";
GRANT USAGE ON DOMAIN dcl_02181_missing_object TO PUBLIC WITH ADMIN OPTION GRANTED BY dcl_02181_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'parameter_privilege' AS privilege_scope;
DROP DOMAIN IF EXISTS dcl_02181_domain;
DROP OWNED BY "dcl_02181_Grantee";
DROP OWNED BY dcl_02181_member;
DROP OWNED BY dcl_02181_grantor;
DROP ROLE IF EXISTS dcl_02181_member;
DROP ROLE IF EXISTS dcl_02181_grantor;
DROP ROLE IF EXISTS "dcl_02181_Grantee";
