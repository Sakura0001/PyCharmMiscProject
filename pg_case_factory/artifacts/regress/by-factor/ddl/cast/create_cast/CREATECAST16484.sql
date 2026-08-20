-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE CAST target_action=with_inout
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATECAST16484
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/create_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/create_cast.yaml
-- primary_obligation_id: CCAST-EXT|16484|pg_cast_catalog_query|DROP_CAST
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (bigint AS createcast_16484_targettype);
DROP CAST IF EXISTS (createcast_16484_targettype AS bigint);
DROP FUNCTION IF EXISTS createcast_16484_revcastfn;
DROP TYPE IF EXISTS createcast_16484_targettype;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createcast_16484_targettype AS ENUM ('a', 'b');
CREATE CAST (createcast_16484_targettype AS bigint) WITH INOUT;
-- 3. 执行唯一获得覆盖信用的 CREATE CAST。
-- primary-target-begin
CREATE CAST (bigint AS createcast_16484_targettype) WITH INOUT AS ASSIGNMENT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS cast_state FROM pg_catalog.pg_cast WHERE castsource = 'bigint'::regtype AND casttarget = 'createcast_16484_targettype'::regtype ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP CAST (bigint AS createcast_16484_targettype);
DROP CAST (createcast_16484_targettype AS bigint);
DROP FUNCTION IF EXISTS createcast_16484_revcastfn;
DROP TYPE IF EXISTS createcast_16484_targettype;
