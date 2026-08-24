-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_13 (tablespace) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
-- factor expected_status=success
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS "dcl_12217_Grantee";
DROP ROLE IF EXISTS dcl_12217_grantor;
DROP ROLE IF EXISTS dcl_12217_member;
CREATE ROLE "dcl_12217_Grantee";
CREATE ROLE dcl_12217_grantor;
CREATE ROLE dcl_12217_member;
GRANT CREATE ON TABLESPACE dcl_12217_tablespace TO "dcl_12217_Grantee";
GRANT CREATE ON TABLESPACE dcl_12217_tablespace TO dcl_12217_grantor WITH GRANT OPTION;
SET ROLE dcl_12217_grantor;
REVOKE CREATE ON TABLESPACE dcl_12217_tablespace FROM "dcl_12217_Grantee" RESTRICT;
RESET ROLE;
SELECT has_tablespace_privilege(CURRENT_USER, 'dcl_12217_tablespace', 'CREATE');
RESET ROLE;
RESET ALL;
DROP OWNED BY "dcl_12217_Grantee";
DROP OWNED BY dcl_12217_member;
DROP OWNED BY dcl_12217_grantor;
DROP ROLE IF EXISTS dcl_12217_member;
DROP ROLE IF EXISTS dcl_12217_grantor;
DROP ROLE IF EXISTS "dcl_12217_Grantee";
