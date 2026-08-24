-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=success
-- factor privilege_scope=column_privilege
-- factor grantee_shape=session_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS dcl_07294_schema.dcl_07294_table;
DROP ROLE IF EXISTS dcl_07294_grantee;
DROP ROLE IF EXISTS dcl_07294_grantor;
DROP ROLE IF EXISTS dcl_07294_member;
CREATE ROLE dcl_07294_grantee;
CREATE ROLE dcl_07294_grantor;
CREATE ROLE dcl_07294_member;
DROP SCHEMA IF EXISTS dcl_07294_schema CASCADE;
CREATE SCHEMA dcl_07294_schema;
CREATE TABLE dcl_07294_schema.dcl_07294_table (id integer, payload text);
GRANT SELECT (payload) ON TABLE dcl_07294_schema.dcl_07294_table TO SESSION_USER;
REVOKE GRANT OPTION FOR SELECT (payload) ON TABLE dcl_07294_schema.dcl_07294_table FROM SESSION_USER RESTRICT;
SELECT count(*) AS table_count FROM dcl_07294_schema.dcl_07294_table;
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_07294_schema CASCADE;
DROP OWNED BY dcl_07294_grantee;
DROP OWNED BY dcl_07294_member;
DROP OWNED BY dcl_07294_grantor;
DROP ROLE IF EXISTS dcl_07294_member;
DROP ROLE IF EXISTS dcl_07294_grantor;
DROP ROLE IF EXISTS dcl_07294_grantee;
DROP TABLE IF EXISTS dcl_07294_schema.dcl_07294_table;
