-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE column privilege on point
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=revoke
-- factor column_type=point
DROP TABLE IF EXISTS dcl_13683_table;
DROP ROLE IF EXISTS dcl_13683_grantee;
CREATE ROLE dcl_13683_grantee;
CREATE TABLE dcl_13683_table (id integer, payload point);
GRANT SELECT (payload) ON TABLE dcl_13683_table TO dcl_13683_grantee;
REVOKE SELECT (payload) ON TABLE dcl_13683_table FROM dcl_13683_grantee;
SELECT has_column_privilege('dcl_13683_grantee', 'dcl_13683_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13683_table;
DROP ROLE IF EXISTS dcl_13683_grantee;
DROP TABLE IF EXISTS dcl_13683_table;
