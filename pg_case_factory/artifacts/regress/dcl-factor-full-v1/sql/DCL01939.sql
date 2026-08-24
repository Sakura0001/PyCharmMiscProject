-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_5 (domain) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=public
-- factor grant_option_shape=admin_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_01939_grantor;
DROP ROLE IF EXISTS dcl_01939_member;
CREATE ROLE dcl_01939_grantor;
CREATE ROLE dcl_01939_member;
DROP DOMAIN IF EXISTS dcl_01939_domain;
CREATE DOMAIN dcl_01939_domain AS text;
GRANT USAGE ON DOMAIN dcl_01939_missing_object TO dcl_01939_grantor WITH GRANT OPTION;
GRANT dcl_01939_grantor TO dcl_01939_member WITH SET TRUE;
SET ROLE dcl_01939_member;
SET ROLE dcl_01939_grantor;
GRANT USAGE ON DOMAIN dcl_01939_missing_object TO PUBLIC WITH ADMIN OPTION;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_01939_domain', 'USAGE');
RESET ROLE;
RESET ALL;
DROP DOMAIN IF EXISTS dcl_01939_domain;
DROP OWNED BY dcl_01939_member;
DROP OWNED BY dcl_01939_grantor;
DROP ROLE IF EXISTS dcl_01939_member;
DROP ROLE IF EXISTS dcl_01939_grantor;
