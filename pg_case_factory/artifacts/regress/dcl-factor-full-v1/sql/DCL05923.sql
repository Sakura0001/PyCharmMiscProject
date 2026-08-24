-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_14 (type) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS dcl_05923_grantor;
DROP ROLE IF EXISTS dcl_05923_member;
CREATE ROLE dcl_05923_grantor;
CREATE ROLE dcl_05923_member;
DROP TYPE IF EXISTS dcl_05923_type;
CREATE TYPE dcl_05923_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_05923_missing_object TO dcl_05923_grantor WITH GRANT OPTION;
GRANT dcl_05923_grantor TO dcl_05923_member WITH SET TRUE;
SET ROLE dcl_05923_member;
SET ROLE dcl_05923_grantor;
GRANT USAGE ON TYPE dcl_05923_missing_object TO PUBLIC;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_05923_type', 'USAGE');
RESET ROLE;
RESET ALL;
DROP TYPE IF EXISTS dcl_05923_type;
DROP OWNED BY dcl_05923_member;
DROP OWNED BY dcl_05923_grantor;
DROP ROLE IF EXISTS dcl_05923_member;
DROP ROLE IF EXISTS dcl_05923_grantor;
