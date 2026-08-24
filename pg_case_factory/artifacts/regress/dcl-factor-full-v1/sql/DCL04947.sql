-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_11 (parameter) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_11
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=current_role
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_04947_Grantee";
DROP ROLE IF EXISTS dcl_04947_grantor;
DROP ROLE IF EXISTS dcl_04947_member;
CREATE ROLE "dcl_04947_Grantee";
CREATE ROLE dcl_04947_grantor;
CREATE ROLE dcl_04947_member;
SET ROLE "dcl_04947_Grantee";
GRANT SELECT ON PARAMETER work_mem TO CURRENT_ROLE GRANTED BY dcl_04947_grantor;
RESET ROLE;
SELECT has_parameter_privilege(CURRENT_USER, 'work_mem', 'SET');
DROP OWNED BY "dcl_04947_Grantee";
DROP OWNED BY dcl_04947_member;
DROP OWNED BY dcl_04947_grantor;
DROP ROLE IF EXISTS dcl_04947_member;
DROP ROLE IF EXISTS dcl_04947_grantor;
DROP ROLE IF EXISTS "dcl_04947_Grantee";
