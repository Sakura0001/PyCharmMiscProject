-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER USER MAPPING server_dependency=server_missing
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERUSERMAPPING01490
-- source_md: skills/pg-sql-generation/references/statements/ddl/user_mapping/alter_user_mapping.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user_mapping/alter_user_mapping.yaml
-- primary_obligation_id: AUM-EXT|01490|option_query|revert_option
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SERVER IF EXISTS alterusermapping_01490_no_such_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterusermapping_01490_fdw;
DROP OWNED BY alterusermapping_01490_mappeduser CASCADE;
DROP ROLE IF EXISTS alterusermapping_01490_mappeduser;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS target_foreign_server_intentionally_absent;
CREATE ROLE alterusermapping_01490_mappeduser LOGIN;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER USER MAPPING。
-- primary-target-begin
ALTER USER MAPPING FOR alterusermapping_01490_mappeduser SERVER alterusermapping_01490_no_such_server OPTIONS (ADD alterusermapping_01490_opt 'val');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS mapping_state FROM pg_catalog.pg_user_mapping WHERE umserver = (SELECT oid FROM pg_catalog.pg_foreign_server WHERE srvname = 'alterusermapping_01490_no_such_server') ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP SERVER IF EXISTS alterusermapping_01490_no_such_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterusermapping_01490_fdw;
DROP OWNED BY alterusermapping_01490_mappeduser CASCADE;
DROP ROLE IF EXISTS alterusermapping_01490_mappeduser;
