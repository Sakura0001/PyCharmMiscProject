-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on text
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=text
DROP TABLE IF EXISTS dcl_13588_table;
DROP ROLE IF EXISTS dcl_13588_grantee;
CREATE ROLE dcl_13588_grantee;
CREATE TABLE dcl_13588_table (id integer, payload text);
GRANT SELECT (payload) ON TABLE dcl_13588_table TO dcl_13588_grantee;
SELECT has_column_privilege('dcl_13588_grantee', 'dcl_13588_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13588_table;
DROP ROLE IF EXISTS dcl_13588_grantee;
DROP TABLE IF EXISTS dcl_13588_table;
