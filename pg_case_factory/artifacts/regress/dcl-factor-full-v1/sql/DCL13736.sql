-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE column privilege on xid8
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=revoke
-- factor column_type=xid8
DROP TABLE IF EXISTS dcl_13736_table;
DROP ROLE IF EXISTS dcl_13736_grantee;
CREATE ROLE dcl_13736_grantee;
CREATE TABLE dcl_13736_table (id integer, payload xid8);
GRANT SELECT (payload) ON TABLE dcl_13736_table TO dcl_13736_grantee;
REVOKE SELECT (payload) ON TABLE dcl_13736_table FROM dcl_13736_grantee;
SELECT has_column_privilege('dcl_13736_grantee', 'dcl_13736_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13736_table;
DROP ROLE IF EXISTS dcl_13736_grantee;
DROP TABLE IF EXISTS dcl_13736_table;
