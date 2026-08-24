-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TABLESPACE directory_condition=not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETABLESPACE04104
-- source_md: skills/pg-sql-generation/references/statements/ddl/tablespace/create_tablespace.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/tablespace/create_tablespace.yaml
-- primary_obligation_id: CTSP-EXT|04104|error_assertion|filesystem_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 58P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLESPACE IF EXISTS createtablespace_04104_ts;
DROP OWNED BY createtablespace_04104_owner CASCADE;
DROP ROLE IF EXISTS createtablespace_04104_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createtablespace_04104_owner LOGIN;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE TABLESPACE。
-- primary-target-begin
CREATE TABLESPACE createtablespace_04104_ts OWNER createtablespace_04104_owner LOCATION '/tmp/pgcf_ctsp/createtablespace_04104_dir' WITH (seq_page_cost = 1.0, random_page_cost = 4.0);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '58P01' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TABLESPACE IF EXISTS createtablespace_04104_ts;
DROP OWNED BY createtablespace_04104_owner CASCADE;
DROP ROLE IF EXISTS createtablespace_04104_owner;
