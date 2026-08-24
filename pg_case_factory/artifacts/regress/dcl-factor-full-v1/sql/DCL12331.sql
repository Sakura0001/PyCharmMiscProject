-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_13 (tablespace) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS dcl_12331_grantor;
DROP ROLE IF EXISTS dcl_12331_member;
CREATE ROLE dcl_12331_grantor;
CREATE ROLE dcl_12331_member;
GRANT CREATE ON TABLESPACE dcl_12331_missing_object TO CURRENT_ROLE;
GRANT CREATE ON TABLESPACE dcl_12331_missing_object TO dcl_12331_grantor WITH GRANT OPTION;
GRANT dcl_12331_grantor TO dcl_12331_member WITH SET TRUE;
SET ROLE dcl_12331_member;
SET ROLE dcl_12331_grantor;
REVOKE CREATE ON TABLESPACE dcl_12331_missing_object FROM CURRENT_ROLE RESTRICT;
RESET ROLE;
SELECT has_tablespace_privilege(CURRENT_USER, 'dcl_12331_tablespace', 'CREATE');
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_12331_member;
DROP OWNED BY dcl_12331_grantor;
DROP ROLE IF EXISTS dcl_12331_member;
DROP ROLE IF EXISTS dcl_12331_grantor;
