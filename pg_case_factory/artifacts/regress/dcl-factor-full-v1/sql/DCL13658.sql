-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE column privilege on smallint
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=revoke
-- factor column_type=smallint
DROP TABLE IF EXISTS dcl_13658_table;
DROP ROLE IF EXISTS dcl_13658_grantee;
CREATE ROLE dcl_13658_grantee;
CREATE TABLE dcl_13658_table (id integer, payload smallint);
GRANT SELECT (payload) ON TABLE dcl_13658_table TO dcl_13658_grantee;
REVOKE SELECT (payload) ON TABLE dcl_13658_table FROM dcl_13658_grantee;
SELECT has_column_privilege('dcl_13658_grantee', 'dcl_13658_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13658_table;
DROP ROLE IF EXISTS dcl_13658_grantee;
DROP TABLE IF EXISTS dcl_13658_table;
