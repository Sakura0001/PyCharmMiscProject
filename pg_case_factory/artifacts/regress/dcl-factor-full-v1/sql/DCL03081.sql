-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_7 (foreign_server) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
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
DROP ROLE IF EXISTS "dcl_03081_Grantee";
DROP ROLE IF EXISTS dcl_03081_grantor;
DROP ROLE IF EXISTS dcl_03081_member;
CREATE ROLE "dcl_03081_Grantee";
CREATE ROLE dcl_03081_grantor;
CREATE ROLE dcl_03081_member;
DROP SERVER IF EXISTS dcl_03081_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_03081_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_03081_fdw;
CREATE SERVER dcl_03081_server FOREIGN DATA WRAPPER dcl_03081_fdw;
SET ROLE "dcl_03081_Grantee";
GRANT USAGE ON FOREIGN SERVER dcl_03081_missing_object TO PUBLIC WITH ADMIN OPTION GRANTED BY dcl_03081_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'parameter_privilege' AS privilege_scope;
DROP SERVER IF EXISTS dcl_03081_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_03081_fdw CASCADE;
DROP OWNED BY "dcl_03081_Grantee";
DROP OWNED BY dcl_03081_member;
DROP OWNED BY dcl_03081_grantor;
DROP ROLE IF EXISTS dcl_03081_member;
DROP ROLE IF EXISTS dcl_03081_grantor;
DROP ROLE IF EXISTS "dcl_03081_Grantee";
