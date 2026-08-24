-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 DECLARE with statement_branch=branch_1, expected_status=success, cursor_state=declared_open, direction_shape=absolute, hold_scroll_shape=scroll, cursor_name_shape=quoted_identifier, query_shape=simple_select, transaction_context=inside_transaction, dependency_state=ready, invalid_combination=none, position_boundary=after_last, verification_mode=effect_query, cleanup_mode=rollback
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=success
-- factor cursor_state=declared_open
-- factor direction_shape=absolute
-- factor hold_scroll_shape=scroll
-- factor cursor_name_shape=quoted_identifier
-- factor query_shape=simple_select
-- factor transaction_context=inside_transaction
-- factor dependency_state=ready
-- factor invalid_combination=none
-- factor position_boundary=after_last
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP TABLE IF EXISTS cur_00182_table;
CREATE TABLE cur_00182_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00182_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
BEGIN;
DECLARE "cur_00182_Cursor" SCROLL CURSOR FOR SELECT id, payload FROM cur_00182_table ORDER BY id;
FETCH ABSOLUTE 999 FROM "cur_00182_Cursor";
SELECT name, is_holdable, is_scrollable FROM pg_catalog.pg_cursors WHERE name = '"cur_00182_Cursor"' ORDER BY name;
CLOSE "cur_00182_Cursor";
SELECT count(*) AS cursor_effect_rows FROM cur_00182_table;
ROLLBACK;
DROP TABLE IF EXISTS cur_00182_table;
