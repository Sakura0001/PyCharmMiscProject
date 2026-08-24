-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_11 (parameter) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_11
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=session_user
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_11455_grantor;
DROP ROLE IF EXISTS dcl_11455_member;
CREATE ROLE dcl_11455_grantor;
CREATE ROLE dcl_11455_member;
GRANT SELECT ON PARAMETER work_mem TO SESSION_USER;
GRANT SELECT ON PARAMETER work_mem TO dcl_11455_grantor WITH GRANT OPTION;
GRANT dcl_11455_grantor TO dcl_11455_member WITH SET TRUE;
SET ROLE dcl_11455_member;
SET ROLE dcl_11455_grantor;
REVOKE SELECT ON PARAMETER work_mem FROM SESSION_USER RESTRICT;
RESET ROLE;
SELECT has_parameter_privilege(CURRENT_USER, 'work_mem', 'SET');
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_11455_member;
DROP OWNED BY dcl_11455_grantor;
DROP ROLE IF EXISTS dcl_11455_member;
DROP ROLE IF EXISTS dcl_11455_grantor;
