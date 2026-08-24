-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TABLESPACE tablespace_name_shape=simple_id
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETABLESPACE00057
-- source_md: skills/pg-sql-generation/references/statements/ddl/tablespace/create_tablespace.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/tablespace/create_tablespace.yaml
-- primary_obligation_id: CTSP-SFV|sfv-24e05e15a2cb74f2b7aba915|create
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLESPACE IF EXISTS createtablespace_00057_ts;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
-- 3. 执行唯一获得覆盖信用的 CREATE TABLESPACE。
-- primary-target-begin
CREATE TABLESPACE createtablespace_00057_ts LOCATION '/tmp/pgcf_ctsp/createtablespace_00057_dir';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS tablespace_state FROM pg_catalog.pg_tablespace WHERE spcname = 'createtablespace_00057_ts' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLESPACE IF EXISTS createtablespace_00057_ts;
