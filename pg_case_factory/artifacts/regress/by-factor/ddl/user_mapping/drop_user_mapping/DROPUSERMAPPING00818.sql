-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP USER MAPPING server_existence=server_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPUSERMAPPING00818
-- source_md: skills/pg-sql-generation/references/statements/ddl/user_mapping/drop_user_mapping.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user_mapping/drop_user_mapping.yaml
-- primary_obligation_id: DROPUSERMAPPING-EXT|00818|drop_user_mapping|notice_assertion|drop_user_mapping
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS no_server_cleanup;
DROP OWNED BY dropusermapping_00818_actor;
DROP ROLE IF EXISTS dropusermapping_00818_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地映射和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE EXTENSION IF NOT EXISTS file_fdw;
CREATE ROLE dropusermapping_00818_actor LOGIN NOSUPERUSER;
SET ROLE dropusermapping_00818_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP USER MAPPING。
-- primary-target-begin
DROP USER MAPPING IF EXISTS FOR PUBLIC SERVER dropusermapping_00818_srv;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS mapping_absent FROM pg_catalog.pg_user_mapping um JOIN pg_catalog.pg_foreign_server s ON um.umserver = s.oid WHERE um.umuser = 0 AND s.srvname = 'dropusermapping_00818_srv' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
SELECT 1 AS no_server_cleanup;
DROP OWNED BY dropusermapping_00818_actor;
DROP ROLE IF EXISTS dropusermapping_00818_actor;
