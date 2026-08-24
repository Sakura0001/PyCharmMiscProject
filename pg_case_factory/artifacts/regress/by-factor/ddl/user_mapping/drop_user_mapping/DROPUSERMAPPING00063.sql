-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP USER MAPPING authorization_path=non_privileged
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPUSERMAPPING00063
-- source_md: skills/pg-sql-generation/references/statements/ddl/user_mapping/drop_user_mapping.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user_mapping/drop_user_mapping.yaml
-- primary_obligation_id: DROPUSERMAPPING-EXT|00063|drop_user_mapping|notice_assertion|drop_server
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP USER MAPPING IF EXISTS FOR dropusermapping_00063_actor SERVER dropusermapping_00063_srv;
DROP OWNED BY dropusermapping_00063_actor;
DROP ROLE IF EXISTS dropusermapping_00063_actor;
DROP USER MAPPING IF EXISTS FOR dropusermapping_00063_role SERVER dropusermapping_00063_srv;
DROP OWNED BY dropusermapping_00063_role;
DROP ROLE IF EXISTS dropusermapping_00063_role;
DROP SERVER IF EXISTS dropusermapping_00063_srv;
\set ON_ERROR_STOP on
-- 2. 创建完整本地映射和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE EXTENSION IF NOT EXISTS file_fdw;
CREATE SERVER dropusermapping_00063_srv FOREIGN DATA WRAPPER file_fdw;
CREATE ROLE dropusermapping_00063_actor LOGIN NOSUPERUSER;
CREATE ROLE dropusermapping_00063_role LOGIN;
SET ROLE dropusermapping_00063_actor;
CREATE USER MAPPING FOR dropusermapping_00063_role SERVER dropusermapping_00063_srv;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP USER MAPPING。
-- primary-target-begin
DROP USER MAPPING FOR dropusermapping_00063_role SERVER dropusermapping_00063_srv;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS mapping_present FROM pg_catalog.pg_user_mapping um JOIN pg_catalog.pg_authid a ON um.umuser = a.oid JOIN pg_catalog.pg_foreign_server s ON um.umserver = s.oid WHERE a.rolname = 'dropusermapping_00063_role' AND s.srvname = 'dropusermapping_00063_srv' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP USER MAPPING IF EXISTS FOR dropusermapping_00063_actor SERVER dropusermapping_00063_srv;
DROP OWNED BY dropusermapping_00063_actor;
DROP ROLE IF EXISTS dropusermapping_00063_actor;
DROP USER MAPPING IF EXISTS FOR dropusermapping_00063_role SERVER dropusermapping_00063_srv;
DROP OWNED BY dropusermapping_00063_role;
DROP ROLE IF EXISTS dropusermapping_00063_role;
DROP SERVER IF EXISTS dropusermapping_00063_srv;
