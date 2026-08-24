-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on inet
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=inet
DROP TABLE IF EXISTS dcl_13606_table;
DROP ROLE IF EXISTS dcl_13606_grantee;
CREATE ROLE dcl_13606_grantee;
CREATE TABLE dcl_13606_table (id integer, payload inet);
GRANT SELECT (payload) ON TABLE dcl_13606_table TO dcl_13606_grantee;
SELECT has_column_privilege('dcl_13606_grantee', 'dcl_13606_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13606_table;
DROP ROLE IF EXISTS dcl_13606_grantee;
DROP TABLE IF EXISTS dcl_13606_table;
