-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER USER MAPPING invalid_option=invalid_option_name
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERUSERMAPPING00011
-- source_md: skills/pg-sql-generation/references/statements/ddl/user_mapping/alter_user_mapping.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user_mapping/alter_user_mapping.yaml
-- primary_obligation_id: AUM-SFV|sfv-e19c4c760f66a99fa72fc2d1|options
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
ALTER USER MAPPING FOR alterusermapping_00011_mappeduser SERVER alterusermapping_00011_server OPTIONS (DROP alterusermapping_00011_opt);
DROP USER MAPPING IF EXISTS FOR alterusermapping_00011_mappeduser SERVER alterusermapping_00011_server;
DROP SERVER IF EXISTS alterusermapping_00011_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterusermapping_00011_fdw;
DROP OWNED BY alterusermapping_00011_mappeduser CASCADE;
DROP ROLE IF EXISTS alterusermapping_00011_mappeduser;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FOREIGN DATA WRAPPER alterusermapping_00011_fdw;
CREATE SERVER alterusermapping_00011_server FOREIGN DATA WRAPPER alterusermapping_00011_fdw;
CREATE ROLE alterusermapping_00011_mappeduser LOGIN;
CREATE USER MAPPING FOR alterusermapping_00011_mappeduser SERVER alterusermapping_00011_server OPTIONS (ADD alterusermapping_00011_opt 'initial');
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER USER MAPPING。
-- primary-target-begin
ALTER USER MAPPING FOR alterusermapping_00011_mappeduser SERVER alterusermapping_00011_server OPTIONS (ADD alterusermapping_00011_bogus_opt 'val');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS mapping_state FROM pg_catalog.pg_user_mapping WHERE umserver = (SELECT oid FROM pg_catalog.pg_foreign_server WHERE srvname = 'alterusermapping_00011_server') ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP USER MAPPING IF EXISTS FOR alterusermapping_00011_mappeduser SERVER alterusermapping_00011_server;
DROP SERVER IF EXISTS alterusermapping_00011_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterusermapping_00011_fdw;
DROP OWNED BY alterusermapping_00011_mappeduser CASCADE;
DROP ROLE IF EXISTS alterusermapping_00011_mappeduser;
