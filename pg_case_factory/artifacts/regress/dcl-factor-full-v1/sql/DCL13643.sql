-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on regnamespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=regnamespace
DROP TABLE IF EXISTS dcl_13643_table;
DROP ROLE IF EXISTS dcl_13643_grantee;
CREATE ROLE dcl_13643_grantee;
CREATE TABLE dcl_13643_table (id integer, payload regnamespace);
GRANT SELECT (payload) ON TABLE dcl_13643_table TO dcl_13643_grantee;
SELECT has_column_privilege('dcl_13643_grantee', 'dcl_13643_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13643_table;
DROP ROLE IF EXISTS dcl_13643_grantee;
DROP TABLE IF EXISTS dcl_13643_table;
