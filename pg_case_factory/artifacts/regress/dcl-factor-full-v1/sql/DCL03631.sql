-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_9 (language) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_9
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS "dcl_03631_Grantee";
DROP ROLE IF EXISTS dcl_03631_grantor;
DROP ROLE IF EXISTS dcl_03631_member;
CREATE ROLE "dcl_03631_Grantee";
CREATE ROLE dcl_03631_grantor;
CREATE ROLE dcl_03631_member;
GRANT USAGE ON LANGUAGE plpgsql TO dcl_03631_grantor WITH GRANT OPTION;
SET ROLE dcl_03631_grantor;
GRANT USAGE ON LANGUAGE plpgsql TO "dcl_03631_Grantee";
RESET ROLE;
SELECT has_language_privilege(CURRENT_USER, 'plpgsql', 'USAGE');
RESET ROLE;
RESET ALL;
DROP OWNED BY "dcl_03631_Grantee";
DROP OWNED BY dcl_03631_member;
DROP OWNED BY dcl_03631_grantor;
DROP ROLE IF EXISTS dcl_03631_member;
DROP ROLE IF EXISTS dcl_03631_grantor;
DROP ROLE IF EXISTS "dcl_03631_Grantee";
