-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TABLESPACE verification_mode=error_assertion
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTABLESPACE00072
-- source_md: skills/pg-sql-generation/references/statements/ddl/tablespace/alter_tablespace.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/tablespace/alter_tablespace.yaml
-- primary_obligation_id: ATSP-SFV|sfv-112106e3667eb37631de9c17|rename
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLESPACE IF EXISTS alter_tablespace_00072_ts;
DROP TABLESPACE IF EXISTS alter_tablespace_00072_newts;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLESPACE alter_tablespace_00072_ts LOCATION '/tmp/pgcf_tablespace_location';
-- 3. 执行唯一获得覆盖信用的 ALTER TABLESPACE。
-- primary-target-begin
ALTER TABLESPACE alter_tablespace_00072_ts RENAME TO alter_tablespace_00072_newts;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TABLESPACE IF EXISTS alter_tablespace_00072_ts;
DROP TABLESPACE IF EXISTS alter_tablespace_00072_newts;
