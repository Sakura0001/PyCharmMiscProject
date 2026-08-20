-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : COMMIT PREPARED transaction_state=savepoint_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: COMMITPREPARED02484
-- source_md: skills/pg-sql-generation/references/statements/tcl/two_phase_transaction/commit_prepared.md
-- factor_md: skills/pg-sql-generation/references/combinations/tcl/two_phase_transaction/commit_prepared.yaml
-- primary_obligation_id: CPREP-EXT|02484|effect_query|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 25001
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS commitprepared_02484_data;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE commitprepared_02484_data (id integer, payload text);
INSERT INTO commitprepared_02484_data VALUES (1, 'commit_prepared_fixture');
BEGIN;
SAVEPOINT commitprepared_02484_sp;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 COMMIT PREPARED。
-- primary-target-begin
COMMIT PREPARED 'commitprepared_02484_Mixed Tx';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '25001' AS target_sqlstate_matches_expected;
SELECT count(*) AS committed_rows FROM commitprepared_02484_data ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS commitprepared_02484_data;
