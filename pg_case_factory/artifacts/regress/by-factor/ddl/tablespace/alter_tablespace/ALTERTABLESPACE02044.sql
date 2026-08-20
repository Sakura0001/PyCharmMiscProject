-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TABLESPACE set_role_capability=cannot_set_role
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTABLESPACE02044
-- source_md: skills/pg-sql-generation/references/statements/ddl/tablespace/alter_tablespace.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/tablespace/alter_tablespace.yaml
-- primary_obligation_id: ATSP-EXT|02044|effect_query|revert_owner
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLESPACE IF EXISTS alter_tablespace_02044_ts;
DROP OWNED BY alter_tablespace_02044_tsowner CASCADE;
DROP ROLE IF EXISTS alter_tablespace_02044_tsowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alter_tablespace_02044_tsowner LOGIN;
CREATE TABLESPACE alter_tablespace_02044_ts LOCATION '/tmp/pgcf_tablespace_location';
ALTER TABLESPACE alter_tablespace_02044_ts OWNER TO alter_tablespace_02044_tsowner;
SET ROLE alter_tablespace_02044_tsowner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLESPACE。
-- primary-target-begin
ALTER TABLESPACE alter_tablespace_02044_ts OWNER TO CURRENT_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS tablespace_state FROM pg_catalog.pg_tablespace WHERE spcname = 'alter_tablespace_02044_ts' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TABLESPACE IF EXISTS alter_tablespace_02044_ts;
DROP OWNED BY alter_tablespace_02044_tsowner CASCADE;
DROP ROLE IF EXISTS alter_tablespace_02044_tsowner;
