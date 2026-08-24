-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on regoper
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=regoper
DROP TABLE IF EXISTS dcl_13644_table;
DROP ROLE IF EXISTS dcl_13644_grantee;
CREATE ROLE dcl_13644_grantee;
CREATE TABLE dcl_13644_table (id integer, payload regoper);
GRANT SELECT (payload) ON TABLE dcl_13644_table TO dcl_13644_grantee;
SELECT has_column_privilege('dcl_13644_grantee', 'dcl_13644_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13644_table;
DROP ROLE IF EXISTS dcl_13644_grantee;
DROP TABLE IF EXISTS dcl_13644_table;
