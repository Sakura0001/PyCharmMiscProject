-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TABLESPACE target_action=rename
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTABLESPACE03107
-- source_md: skills/pg-sql-generation/references/statements/ddl/tablespace/alter_tablespace.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/tablespace/alter_tablespace.yaml
-- primary_obligation_id: ATSP-EXT|03107|catalog_query_pg_tablespace|role_cleanup
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLESPACE IF EXISTS alter_tablespace_03107_ts;
DROP TABLESPACE IF EXISTS "alter_tablespace_03107_Mixed New";
DROP OWNED BY alter_tablespace_03107_tsowner CASCADE;
DROP ROLE IF EXISTS alter_tablespace_03107_tsowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alter_tablespace_03107_tsowner LOGIN;
CREATE TABLESPACE alter_tablespace_03107_ts LOCATION '/tmp/pgcf_tablespace_location';
ALTER TABLESPACE alter_tablespace_03107_ts OWNER TO alter_tablespace_03107_tsowner;
SET ROLE alter_tablespace_03107_tsowner;
-- 3. 执行唯一获得覆盖信用的 ALTER TABLESPACE。
-- primary-target-begin
ALTER TABLESPACE alter_tablespace_03107_ts RENAME TO "alter_tablespace_03107_Mixed New";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS tablespace_state FROM pg_catalog.pg_tablespace WHERE spcname = 'alter_tablespace_03107_Mixed New' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TABLESPACE IF EXISTS alter_tablespace_03107_ts;
DROP TABLESPACE IF EXISTS "alter_tablespace_03107_Mixed New";
DROP OWNED BY alter_tablespace_03107_tsowner CASCADE;
DROP ROLE IF EXISTS alter_tablespace_03107_tsowner;
