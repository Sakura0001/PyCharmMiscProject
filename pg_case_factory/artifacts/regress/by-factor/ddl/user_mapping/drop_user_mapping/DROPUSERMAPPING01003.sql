-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP USER MAPPING object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPUSERMAPPING01003
-- source_md: skills/pg-sql-generation/references/statements/ddl/user_mapping/drop_user_mapping.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user_mapping/drop_user_mapping.yaml
-- primary_obligation_id: DROPUSERMAPPING-EXT|01003|drop_user_mapping|catalog_query|drop_fdw
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP USER MAPPING IF EXISTS FOR dropusermapping_01003_actor SERVER dropusermapping_01003_srv;
DROP OWNED BY dropusermapping_01003_actor;
DROP ROLE IF EXISTS dropusermapping_01003_actor;
DROP SERVER IF EXISTS dropusermapping_01003_srv;
\set ON_ERROR_STOP on
-- 2. 创建完整本地映射和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE EXTENSION IF NOT EXISTS file_fdw;
CREATE SERVER dropusermapping_01003_srv FOREIGN DATA WRAPPER file_fdw;
CREATE ROLE dropusermapping_01003_actor LOGIN NOSUPERUSER;
GRANT USAGE ON FOREIGN SERVER dropusermapping_01003_srv TO dropusermapping_01003_actor;
SET ROLE dropusermapping_01003_actor;
SELECT 1 AS target_mapping_intentionally_absent;
-- 3. 执行唯一获得覆盖信用的 DROP USER MAPPING。
-- primary-target-begin
DROP USER MAPPING IF EXISTS FOR CURRENT_ROLE SERVER dropusermapping_01003_srv;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS mapping_absent FROM pg_catalog.pg_user_mapping um JOIN pg_catalog.pg_authid a ON um.umuser = a.oid JOIN pg_catalog.pg_foreign_server s ON um.umserver = s.oid WHERE a.rolname = 'dropusermapping_01003_actor' AND s.srvname = 'dropusermapping_01003_srv' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP USER MAPPING IF EXISTS FOR dropusermapping_01003_actor SERVER dropusermapping_01003_srv;
DROP OWNED BY dropusermapping_01003_actor;
DROP ROLE IF EXISTS dropusermapping_01003_actor;
DROP SERVER IF EXISTS dropusermapping_01003_srv;
