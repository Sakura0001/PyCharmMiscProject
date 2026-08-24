-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : ROLLBACK PREPARED target_action=rollback_prepared
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ROLLBACKPREPARED12010
-- source_md: skills/pg-sql-generation/references/statements/tcl/two_phase_transaction/rollback_prepared.md
-- factor_md: skills/pg-sql-generation/references/combinations/tcl/two_phase_transaction/rollback_prepared.yaml
-- primary_obligation_id: ROLLBACKPREPARED-EXT|12010|catalog_query|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS rollbackprepared_12010_data;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE rollbackprepared_12010_data (id integer, payload text);
INSERT INTO rollbackprepared_12010_data VALUES (1, 'rollback_prepared_fixture');
BEGIN;
INSERT INTO rollbackprepared_12010_data VALUES (2, 'prepared_row');
PREPARE TRANSACTION 'rollbackprepared_12010_duptx';
-- 3. 执行唯一获得覆盖信用的 ROLLBACK PREPARED。
-- primary-target-begin
ROLLBACK PREPARED 'rollbackprepared_12010_duptx';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS prepared_residual FROM pg_catalog.pg_prepared_xacts ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS rollbackprepared_12010_data;
