-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_9 (language) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_9
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=public
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_10425_Grantee";
DROP ROLE IF EXISTS dcl_10425_grantor;
DROP ROLE IF EXISTS dcl_10425_member;
CREATE ROLE "dcl_10425_Grantee";
CREATE ROLE dcl_10425_grantor;
CREATE ROLE dcl_10425_member;
GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC;
GRANT USAGE ON LANGUAGE plpgsql TO dcl_10425_grantor WITH GRANT OPTION;
SET ROLE dcl_10425_grantor;
REVOKE USAGE ON LANGUAGE plpgsql FROM PUBLIC GRANTED BY dcl_10425_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
DROP OWNED BY "dcl_10425_Grantee";
DROP OWNED BY dcl_10425_member;
DROP OWNED BY dcl_10425_grantor;
DROP ROLE IF EXISTS dcl_10425_member;
DROP ROLE IF EXISTS dcl_10425_grantor;
DROP ROLE IF EXISTS "dcl_10425_Grantee";
