-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_13 (tablespace) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS dcl_05551_grantor;
DROP ROLE IF EXISTS dcl_05551_member;
CREATE ROLE dcl_05551_grantor;
CREATE ROLE dcl_05551_member;
GRANT CREATE ON TABLESPACE dcl_05551_missing_object TO dcl_05551_grantor WITH GRANT OPTION;
GRANT dcl_05551_grantor TO dcl_05551_member WITH SET TRUE;
SET ROLE dcl_05551_member;
SET ROLE dcl_05551_grantor;
GRANT CREATE ON TABLESPACE dcl_05551_missing_object TO CURRENT_ROLE WITH ADMIN OPTION;
RESET ROLE;
SELECT has_tablespace_privilege(CURRENT_USER, 'dcl_05551_tablespace', 'CREATE');
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_05551_member;
DROP OWNED BY dcl_05551_grantor;
DROP ROLE IF EXISTS dcl_05551_member;
DROP ROLE IF EXISTS dcl_05551_grantor;
