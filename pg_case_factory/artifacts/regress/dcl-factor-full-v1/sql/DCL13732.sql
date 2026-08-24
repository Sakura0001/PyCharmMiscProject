-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE column privilege on regprocedure
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=revoke
-- factor column_type=regprocedure
DROP TABLE IF EXISTS dcl_13732_table;
DROP ROLE IF EXISTS dcl_13732_grantee;
CREATE ROLE dcl_13732_grantee;
CREATE TABLE dcl_13732_table (id integer, payload regprocedure);
GRANT SELECT (payload) ON TABLE dcl_13732_table TO dcl_13732_grantee;
REVOKE SELECT (payload) ON TABLE dcl_13732_table FROM dcl_13732_grantee;
SELECT has_column_privilege('dcl_13732_grantee', 'dcl_13732_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13732_table;
DROP ROLE IF EXISTS dcl_13732_grantee;
DROP TABLE IF EXISTS dcl_13732_table;
