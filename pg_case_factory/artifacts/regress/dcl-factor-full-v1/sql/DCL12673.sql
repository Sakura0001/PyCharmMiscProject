-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_14 (type) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS "dcl_12673_Grantee";
DROP ROLE IF EXISTS dcl_12673_grantor;
DROP ROLE IF EXISTS dcl_12673_member;
CREATE ROLE "dcl_12673_Grantee";
CREATE ROLE dcl_12673_grantor;
CREATE ROLE dcl_12673_member;
DROP TYPE IF EXISTS dcl_12673_type;
CREATE TYPE dcl_12673_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_12673_type TO PUBLIC;
GRANT USAGE ON TYPE dcl_12673_type TO dcl_12673_grantor WITH GRANT OPTION;
SET ROLE dcl_12673_grantor;
REVOKE USAGE ON TYPE dcl_12673_type FROM PUBLIC RESTRICT;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_12673_type', 'USAGE');
RESET ROLE;
RESET ALL;
DROP TYPE IF EXISTS dcl_12673_type;
DROP OWNED BY "dcl_12673_Grantee";
DROP OWNED BY dcl_12673_member;
DROP OWNED BY dcl_12673_grantor;
DROP ROLE IF EXISTS dcl_12673_member;
DROP ROLE IF EXISTS dcl_12673_grantor;
DROP ROLE IF EXISTS "dcl_12673_Grantee";
