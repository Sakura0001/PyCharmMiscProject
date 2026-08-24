-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TABLESPACE tablespace_name_shape=invalid_name
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTABLESPACE06142
-- source_md: skills/pg-sql-generation/references/statements/ddl/tablespace/alter_tablespace.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/tablespace/alter_tablespace.yaml
-- primary_obligation_id: ATSP-EXT|06142|effect_query|role_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 42601
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLESPACE IF EXISTS alter_tablespace_06142_bad-ts;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLESPACE alter_tablespace_06142_bad-ts LOCATION '/tmp/pgcf_tablespace_location';
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLESPACE。
-- primary-target-begin
ALTER TABLESPACE alter_tablespace_06142_bad-ts SET (seq_page_cost = 1.0);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42601' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS tablespace_state FROM pg_catalog.pg_tablespace WHERE spcname = 'alter_tablespace_06142_bad-ts' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLESPACE IF EXISTS alter_tablespace_06142_bad-ts;
