-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE column privilege on character
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=revoke
-- factor column_type=character
DROP TABLE IF EXISTS dcl_13671_table;
DROP ROLE IF EXISTS dcl_13671_grantee;
CREATE ROLE dcl_13671_grantee;
CREATE TABLE dcl_13671_table (id integer, payload character);
GRANT SELECT (payload) ON TABLE dcl_13671_table TO dcl_13671_grantee;
REVOKE SELECT (payload) ON TABLE dcl_13671_table FROM dcl_13671_grantee;
SELECT has_column_privilege('dcl_13671_grantee', 'dcl_13671_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13671_table;
DROP ROLE IF EXISTS dcl_13671_grantee;
DROP TABLE IF EXISTS dcl_13671_table;
