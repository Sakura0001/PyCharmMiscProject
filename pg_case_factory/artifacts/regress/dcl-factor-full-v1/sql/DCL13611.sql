-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on tsvector
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=tsvector
DROP TABLE IF EXISTS dcl_13611_table;
DROP ROLE IF EXISTS dcl_13611_grantee;
CREATE ROLE dcl_13611_grantee;
CREATE TABLE dcl_13611_table (id integer, payload tsvector);
GRANT SELECT (payload) ON TABLE dcl_13611_table TO dcl_13611_grantee;
SELECT has_column_privilege('dcl_13611_grantee', 'dcl_13611_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13611_table;
DROP ROLE IF EXISTS dcl_13611_grantee;
DROP TABLE IF EXISTS dcl_13611_table;
