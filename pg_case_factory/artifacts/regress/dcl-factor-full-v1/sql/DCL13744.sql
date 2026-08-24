-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE MAINTAIN privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=revoke
-- factor pg18_privilege=maintain
DROP TABLE IF EXISTS dcl_13744_table;
DROP ROLE IF EXISTS dcl_13744_grantee;
CREATE ROLE dcl_13744_grantee;
CREATE TABLE dcl_13744_table (id integer);
GRANT MAINTAIN ON TABLE dcl_13744_table TO dcl_13744_grantee;
REVOKE MAINTAIN ON TABLE dcl_13744_table FROM dcl_13744_grantee;
SELECT has_table_privilege('dcl_13744_grantee', 'dcl_13744_table', 'MAINTAIN');
DROP TABLE IF EXISTS dcl_13744_table;
DROP ROLE IF EXISTS dcl_13744_grantee;
DROP TABLE IF EXISTS dcl_13744_table;
