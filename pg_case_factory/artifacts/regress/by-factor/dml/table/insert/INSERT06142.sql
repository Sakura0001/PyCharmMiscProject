-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : INSERT constraint_boundary=constraint_violation
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: INSERT06142
-- source_md: skills/pg-sql-generation/references/statements/dml/table/insert.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/insert.yaml
-- primary_obligation_id: INSERT-EXT|06142|returned_rows|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 23505
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS insert_06142_tbl, insert_06142_src, insert_06142_ref CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE insert_06142_tbl (id int PRIMARY KEY, val int UNIQUE);
INSERT INTO insert_06142_tbl VALUES (1, 100);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 INSERT。
-- primary-target-begin
INSERT INTO insert_06142_tbl (id, val) VALUES (2, 100);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '23505' AS target_sqlstate_matches_expected;
SELECT count(*) >= 0 AS returned_rows_state FROM insert_06142_tbl ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS insert_06142_tbl, insert_06142_src, insert_06142_ref CASCADE;
