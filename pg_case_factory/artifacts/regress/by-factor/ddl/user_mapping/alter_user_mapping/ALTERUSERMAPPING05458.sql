-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER USER MAPPING target_action=options
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERUSERMAPPING05458
-- source_md: skills/pg-sql-generation/references/statements/ddl/user_mapping/alter_user_mapping.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user_mapping/alter_user_mapping.yaml
-- primary_obligation_id: AUM-EXT|05458|catalog_query_pg_user_mapping|drop_server
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP USER MAPPING IF EXISTS FOR PUBLIC SERVER alterusermapping_05458_server;
DROP SERVER IF EXISTS alterusermapping_05458_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterusermapping_05458_fdw;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FOREIGN DATA WRAPPER alterusermapping_05458_fdw;
CREATE SERVER alterusermapping_05458_server FOREIGN DATA WRAPPER alterusermapping_05458_fdw;
CREATE USER MAPPING FOR PUBLIC SERVER alterusermapping_05458_server OPTIONS (ADD alterusermapping_05458_opt 'initial');
-- 3. 执行唯一获得覆盖信用的 ALTER USER MAPPING。
-- primary-target-begin
ALTER USER MAPPING FOR PUBLIC SERVER alterusermapping_05458_server OPTIONS (DROP alterusermapping_05458_opt);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS mapping_state FROM pg_catalog.pg_user_mapping WHERE umserver = (SELECT oid FROM pg_catalog.pg_foreign_server WHERE srvname = 'alterusermapping_05458_server') ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP USER MAPPING IF EXISTS FOR PUBLIC SERVER alterusermapping_05458_server;
DROP SERVER IF EXISTS alterusermapping_05458_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterusermapping_05458_fdw;
