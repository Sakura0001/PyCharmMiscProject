-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on smallint
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=smallint
DROP TABLE IF EXISTS dcl_13573_table;
DROP ROLE IF EXISTS dcl_13573_grantee;
CREATE ROLE dcl_13573_grantee;
CREATE TABLE dcl_13573_table (id integer, payload smallint);
GRANT SELECT (payload) ON TABLE dcl_13573_table TO dcl_13573_grantee;
SELECT has_column_privilege('dcl_13573_grantee', 'dcl_13573_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13573_table;
DROP ROLE IF EXISTS dcl_13573_grantee;
DROP TABLE IF EXISTS dcl_13573_table;
