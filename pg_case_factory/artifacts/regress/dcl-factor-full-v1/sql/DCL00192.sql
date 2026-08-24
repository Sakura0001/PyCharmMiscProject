-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_1 (table) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=role_name
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS dcl_00192_table;
DROP ROLE IF EXISTS "dcl_00192_Grantee";
DROP ROLE IF EXISTS dcl_00192_grantor;
DROP ROLE IF EXISTS dcl_00192_member;
CREATE ROLE "dcl_00192_Grantee";
CREATE ROLE dcl_00192_grantor;
CREATE ROLE dcl_00192_member;
CREATE TABLE dcl_00192_table (id integer, payload text);
SET ROLE "dcl_00192_Grantee";
GRANT SELECT ON TABLE dcl_00192_missing_object TO "dcl_00192_Grantee" WITH INHERIT TRUE GRANTED BY dcl_00192_grantor;
RESET ROLE;
SET ROLE "dcl_00192_Grantee";
SELECT count(*) AS privilege_effect_rows FROM dcl_00192_table;
RESET ROLE;
DROP OWNED BY "dcl_00192_Grantee";
DROP OWNED BY dcl_00192_member;
DROP OWNED BY dcl_00192_grantor;
DROP ROLE IF EXISTS dcl_00192_member;
DROP ROLE IF EXISTS dcl_00192_grantor;
DROP ROLE IF EXISTS "dcl_00192_Grantee";
DROP TABLE IF EXISTS dcl_00192_table;
