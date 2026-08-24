-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE column privilege on regrole
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=revoke
-- factor column_type=regrole
DROP TABLE IF EXISTS dcl_13733_table;
DROP ROLE IF EXISTS dcl_13733_grantee;
CREATE ROLE dcl_13733_grantee;
CREATE TABLE dcl_13733_table (id integer, payload regrole);
GRANT SELECT (payload) ON TABLE dcl_13733_table TO dcl_13733_grantee;
REVOKE SELECT (payload) ON TABLE dcl_13733_table FROM dcl_13733_grantee;
SELECT has_column_privilege('dcl_13733_grantee', 'dcl_13733_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13733_table;
DROP ROLE IF EXISTS dcl_13733_grantee;
DROP TABLE IF EXISTS dcl_13733_table;
