-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on domain_type
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=domain_type
DROP TABLE IF EXISTS dcl_13636_table;
DROP ROLE IF EXISTS dcl_13636_grantee;
CREATE ROLE dcl_13636_grantee;
CREATE DOMAIN dcl_13636_domain AS text;
CREATE TABLE dcl_13636_table (id integer, payload dcl_13636_domain);
GRANT SELECT (payload) ON TABLE dcl_13636_table TO dcl_13636_grantee;
SELECT has_column_privilege('dcl_13636_grantee', 'dcl_13636_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13636_table;
DROP DOMAIN IF EXISTS dcl_13636_domain;
DROP ROLE IF EXISTS dcl_13636_grantee;
DROP TABLE IF EXISTS dcl_13636_table;
