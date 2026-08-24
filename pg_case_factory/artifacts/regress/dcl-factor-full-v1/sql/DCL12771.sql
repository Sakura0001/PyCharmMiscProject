-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_14 (type) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS "dcl_12771_Grantee";
DROP ROLE IF EXISTS dcl_12771_grantor;
DROP ROLE IF EXISTS dcl_12771_member;
CREATE ROLE "dcl_12771_Grantee";
CREATE ROLE dcl_12771_grantor;
CREATE ROLE dcl_12771_member;
DROP TYPE IF EXISTS dcl_12771_type;
CREATE TYPE dcl_12771_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_12771_missing_object TO PUBLIC;
SET ROLE "dcl_12771_Grantee";
REVOKE USAGE ON TYPE dcl_12771_missing_object FROM PUBLIC GRANTED BY dcl_12771_grantor RESTRICT;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_12771_type', 'USAGE');
DROP TYPE IF EXISTS dcl_12771_type;
DROP OWNED BY "dcl_12771_Grantee";
DROP OWNED BY dcl_12771_member;
DROP OWNED BY dcl_12771_grantor;
DROP ROLE IF EXISTS dcl_12771_member;
DROP ROLE IF EXISTS dcl_12771_grantor;
DROP ROLE IF EXISTS "dcl_12771_Grantee";
