-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_1 (table) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS dcl_13765_table;
DROP ROLE IF EXISTS dcl_13765_grantee;
DROP ROLE IF EXISTS dcl_13765_grantor;
DROP ROLE IF EXISTS dcl_13765_member;
CREATE ROLE dcl_13765_grantee;
CREATE ROLE dcl_13765_grantor;
CREATE ROLE dcl_13765_member;
CREATE TABLE dcl_13765_table (id integer, payload text);
GRANT EXECUTE ON TABLE dcl_13765_missing_object TO dcl_13765_grantee;
SELECT count(*) AS table_count FROM dcl_13765_table;
DROP OWNED BY dcl_13765_grantee;
DROP OWNED BY dcl_13765_member;
DROP OWNED BY dcl_13765_grantor;
DROP ROLE IF EXISTS dcl_13765_member;
DROP ROLE IF EXISTS dcl_13765_grantor;
DROP ROLE IF EXISTS dcl_13765_grantee;
DROP TABLE IF EXISTS dcl_13765_table;
