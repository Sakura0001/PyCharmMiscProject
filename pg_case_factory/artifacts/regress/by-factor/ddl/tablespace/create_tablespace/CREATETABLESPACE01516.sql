-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TABLESPACE object_state=reserved_name_conflict
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETABLESPACE01516
-- source_md: skills/pg-sql-generation/references/statements/ddl/tablespace/create_tablespace.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/tablespace/create_tablespace.yaml
-- primary_obligation_id: CTSP-EXT|01516|catalog_query_pg_tablespace|role_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 42939
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OWNED BY createtablespace_01516_owner CASCADE;
DROP ROLE IF EXISTS createtablespace_01516_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createtablespace_01516_owner LOGIN;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE TABLESPACE。
-- primary-target-begin
CREATE TABLESPACE pg_createtablespace_01516_ts OWNER createtablespace_01516_owner LOCATION '/tmp/pgcf_ctsp/createtablespace_01516_dir' WITH (seq_page_cost = 1.0, random_page_cost = 4.0);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42939' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS tablespace_state FROM pg_catalog.pg_tablespace WHERE spcname = 'pg_createtablespace_01516_ts' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP OWNED BY createtablespace_01516_owner CASCADE;
DROP ROLE IF EXISTS createtablespace_01516_owner;
