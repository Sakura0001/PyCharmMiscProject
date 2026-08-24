-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on character_varying
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=character_varying
DROP TABLE IF EXISTS dcl_13585_table;
DROP ROLE IF EXISTS dcl_13585_grantee;
CREATE ROLE dcl_13585_grantee;
CREATE TABLE dcl_13585_table (id integer, payload character varying);
GRANT SELECT (payload) ON TABLE dcl_13585_table TO dcl_13585_grantee;
SELECT has_column_privilege('dcl_13585_grantee', 'dcl_13585_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13585_table;
DROP ROLE IF EXISTS dcl_13585_grantee;
DROP TABLE IF EXISTS dcl_13585_table;
