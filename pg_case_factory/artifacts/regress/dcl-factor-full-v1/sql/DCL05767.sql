-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_13 (tablespace) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS dcl_05767_grantor;
DROP ROLE IF EXISTS dcl_05767_member;
CREATE ROLE dcl_05767_grantor;
CREATE ROLE dcl_05767_member;
GRANT CREATE ON TABLESPACE dcl_05767_missing_object TO dcl_05767_grantor WITH GRANT OPTION;
GRANT dcl_05767_grantor TO dcl_05767_member WITH SET TRUE;
SET ROLE dcl_05767_member;
SET ROLE dcl_05767_grantor;
GRANT CREATE ON TABLESPACE dcl_05767_missing_object TO dcl_05767_missing_role WITH ADMIN OPTION;
RESET ROLE;
SELECT has_tablespace_privilege(CURRENT_USER, 'dcl_05767_tablespace', 'CREATE');
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_05767_member;
DROP OWNED BY dcl_05767_grantor;
DROP ROLE IF EXISTS dcl_05767_member;
DROP ROLE IF EXISTS dcl_05767_grantor;
