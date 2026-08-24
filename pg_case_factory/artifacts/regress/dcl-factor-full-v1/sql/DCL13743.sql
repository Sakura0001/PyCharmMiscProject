-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT MAINTAIN privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor pg18_privilege=maintain
DROP TABLE IF EXISTS dcl_13743_table;
DROP ROLE IF EXISTS dcl_13743_grantee;
CREATE ROLE dcl_13743_grantee;
CREATE TABLE dcl_13743_table (id integer);
GRANT MAINTAIN ON TABLE dcl_13743_table TO dcl_13743_grantee;
SELECT has_table_privilege('dcl_13743_grantee', 'dcl_13743_table', 'MAINTAIN');
DROP TABLE IF EXISTS dcl_13743_table;
DROP ROLE IF EXISTS dcl_13743_grantee;
DROP TABLE IF EXISTS dcl_13743_table;
