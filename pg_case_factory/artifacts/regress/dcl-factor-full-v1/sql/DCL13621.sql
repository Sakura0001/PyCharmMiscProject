-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on numeric_array
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=numeric_array
DROP TABLE IF EXISTS dcl_13621_table;
DROP ROLE IF EXISTS dcl_13621_grantee;
CREATE ROLE dcl_13621_grantee;
CREATE TABLE dcl_13621_table (id integer, payload numeric[]);
GRANT SELECT (payload) ON TABLE dcl_13621_table TO dcl_13621_grantee;
SELECT has_column_privilege('dcl_13621_grantee', 'dcl_13621_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13621_table;
DROP ROLE IF EXISTS dcl_13621_grantee;
DROP TABLE IF EXISTS dcl_13621_table;
