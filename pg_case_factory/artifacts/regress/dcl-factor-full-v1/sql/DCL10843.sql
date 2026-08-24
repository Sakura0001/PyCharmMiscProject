-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_9 (language) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_9
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS dcl_10843_grantor;
DROP ROLE IF EXISTS dcl_10843_member;
CREATE ROLE dcl_10843_grantor;
CREATE ROLE dcl_10843_member;
GRANT USAGE ON LANGUAGE plpgsql TO CURRENT_USER;
GRANT USAGE ON LANGUAGE plpgsql TO dcl_10843_grantor WITH GRANT OPTION;
GRANT dcl_10843_grantor TO dcl_10843_member WITH SET TRUE;
SET ROLE dcl_10843_member;
SET ROLE dcl_10843_grantor;
REVOKE USAGE ON LANGUAGE plpgsql FROM CURRENT_USER RESTRICT;
RESET ROLE;
SELECT has_language_privilege(CURRENT_USER, 'plpgsql', 'USAGE');
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_10843_member;
DROP OWNED BY dcl_10843_grantor;
DROP ROLE IF EXISTS dcl_10843_member;
DROP ROLE IF EXISTS dcl_10843_grantor;
