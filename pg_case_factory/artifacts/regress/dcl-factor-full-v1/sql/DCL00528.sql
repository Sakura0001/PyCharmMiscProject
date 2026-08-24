-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_2 (column) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=public
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS dcl_00528_table;
DROP ROLE IF EXISTS "dcl_00528_Grantee";
DROP ROLE IF EXISTS dcl_00528_grantor;
DROP ROLE IF EXISTS dcl_00528_member;
CREATE ROLE "dcl_00528_Grantee";
CREATE ROLE dcl_00528_grantor;
CREATE ROLE dcl_00528_member;
CREATE TABLE dcl_00528_table (id integer, payload text);
SET ROLE "dcl_00528_Grantee";
GRANT EXECUTE (payload) ON TABLE dcl_00528_missing_object TO PUBLIC WITH GRANT OPTION GRANTED BY dcl_00528_grantor;
RESET ROLE;
SELECT count(*) AS privilege_effect_rows FROM dcl_00528_table;
DROP OWNED BY "dcl_00528_Grantee";
DROP OWNED BY dcl_00528_member;
DROP OWNED BY dcl_00528_grantor;
DROP ROLE IF EXISTS dcl_00528_member;
DROP ROLE IF EXISTS dcl_00528_grantor;
DROP ROLE IF EXISTS "dcl_00528_Grantee";
DROP TABLE IF EXISTS dcl_00528_table;
