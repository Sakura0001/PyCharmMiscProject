-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_13 (tablespace) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
-- factor expected_status=success
-- factor privilege_scope=table_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS dcl_13791_grantee;
DROP ROLE IF EXISTS dcl_13791_grantor;
DROP ROLE IF EXISTS dcl_13791_member;
CREATE ROLE dcl_13791_grantee;
CREATE ROLE dcl_13791_grantor;
CREATE ROLE dcl_13791_member;
GRANT CREATE ON TABLESPACE dcl_13791_tablespace TO dcl_13791_grantee;
SELECT has_tablespace_privilege(CURRENT_USER, 'dcl_13791_tablespace', 'CREATE');
DROP OWNED BY dcl_13791_grantee;
DROP OWNED BY dcl_13791_member;
DROP OWNED BY dcl_13791_grantor;
DROP ROLE IF EXISTS dcl_13791_member;
DROP ROLE IF EXISTS dcl_13791_grantor;
DROP ROLE IF EXISTS dcl_13791_grantee;
