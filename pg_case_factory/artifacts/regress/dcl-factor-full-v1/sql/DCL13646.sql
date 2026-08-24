-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on regproc
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=regproc
DROP TABLE IF EXISTS dcl_13646_table;
DROP ROLE IF EXISTS dcl_13646_grantee;
CREATE ROLE dcl_13646_grantee;
CREATE TABLE dcl_13646_table (id integer, payload regproc);
GRANT SELECT (payload) ON TABLE dcl_13646_table TO dcl_13646_grantee;
SELECT has_column_privilege('dcl_13646_grantee', 'dcl_13646_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13646_table;
DROP ROLE IF EXISTS dcl_13646_grantee;
DROP TABLE IF EXISTS dcl_13646_table;
