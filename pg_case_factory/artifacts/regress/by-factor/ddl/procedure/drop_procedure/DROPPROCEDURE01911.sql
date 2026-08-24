-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP PROCEDURE object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPPROCEDURE01911
-- source_md: skills/pg-sql-generation/references/statements/ddl/procedure/drop_procedure.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/procedure/drop_procedure.yaml
-- primary_obligation_id: DROPPROCEDURE-EXT|01911|drop_procedure|pg_proc_catalog_query|DROP_PROCEDURE_if_exists_cascade
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PROCEDURE IF EXISTS "dropprocedure_01911_select"(integer) CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地过程和因子专用夹具。
CREATE PROCEDURE "dropprocedure_01911_select"(integer) AS $$ BEGIN END; $$ LANGUAGE plpgsql;
-- 3. 执行唯一获得覆盖信用的 DROP PROCEDURE。
-- primary-target-begin
DROP PROCEDURE IF EXISTS "dropprocedure_01911_select"(integer);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS procedure_absent FROM pg_catalog.pg_proc WHERE proname = 'dropprocedure_01911_select' AND prokind = 'p' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP PROCEDURE IF EXISTS "dropprocedure_01911_select"(integer) CASCADE;
