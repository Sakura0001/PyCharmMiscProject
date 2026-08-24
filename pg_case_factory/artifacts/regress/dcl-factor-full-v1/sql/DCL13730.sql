-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE column privilege on regoperator
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=revoke
-- factor column_type=regoperator
DROP TABLE IF EXISTS dcl_13730_table;
DROP ROLE IF EXISTS dcl_13730_grantee;
CREATE ROLE dcl_13730_grantee;
CREATE TABLE dcl_13730_table (id integer, payload regoperator);
GRANT SELECT (payload) ON TABLE dcl_13730_table TO dcl_13730_grantee;
REVOKE SELECT (payload) ON TABLE dcl_13730_table FROM dcl_13730_grantee;
SELECT has_column_privilege('dcl_13730_grantee', 'dcl_13730_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13730_table;
DROP ROLE IF EXISTS dcl_13730_grantee;
DROP TABLE IF EXISTS dcl_13730_table;
