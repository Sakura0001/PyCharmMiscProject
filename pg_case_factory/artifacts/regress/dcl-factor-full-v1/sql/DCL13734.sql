-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE column privilege on regtype
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=revoke
-- factor column_type=regtype
DROP TABLE IF EXISTS dcl_13734_table;
DROP ROLE IF EXISTS dcl_13734_grantee;
CREATE ROLE dcl_13734_grantee;
CREATE TABLE dcl_13734_table (id integer, payload regtype);
GRANT SELECT (payload) ON TABLE dcl_13734_table TO dcl_13734_grantee;
REVOKE SELECT (payload) ON TABLE dcl_13734_table FROM dcl_13734_grantee;
SELECT has_column_privilege('dcl_13734_grantee', 'dcl_13734_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13734_table;
DROP ROLE IF EXISTS dcl_13734_grantee;
DROP TABLE IF EXISTS dcl_13734_table;
