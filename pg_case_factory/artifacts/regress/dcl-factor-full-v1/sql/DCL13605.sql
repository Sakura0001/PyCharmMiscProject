-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on cidr
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=cidr
DROP TABLE IF EXISTS dcl_13605_table;
DROP ROLE IF EXISTS dcl_13605_grantee;
CREATE ROLE dcl_13605_grantee;
CREATE TABLE dcl_13605_table (id integer, payload cidr);
GRANT SELECT (payload) ON TABLE dcl_13605_table TO dcl_13605_grantee;
SELECT has_column_privilege('dcl_13605_grantee', 'dcl_13605_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13605_table;
DROP ROLE IF EXISTS dcl_13605_grantee;
DROP TABLE IF EXISTS dcl_13605_table;
