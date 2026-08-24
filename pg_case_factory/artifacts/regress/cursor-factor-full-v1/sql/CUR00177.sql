-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 DECLARE with statement_branch=branch_1, expected_status=success, cursor_state=declared_open, direction_shape=prior, hold_scroll_shape=scroll, cursor_name_shape=plain_identifier, query_shape=ordered_select, transaction_context=inside_transaction, dependency_state=ready, invalid_combination=none, position_boundary=middle, verification_mode=returned_rows, cleanup_mode=drop_objects
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=success
-- factor cursor_state=declared_open
-- factor direction_shape=prior
-- factor hold_scroll_shape=scroll
-- factor cursor_name_shape=plain_identifier
-- factor query_shape=ordered_select
-- factor transaction_context=inside_transaction
-- factor dependency_state=ready
-- factor invalid_combination=none
-- factor position_boundary=middle
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS cur_00177_table;
CREATE TABLE cur_00177_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00177_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
BEGIN;
DECLARE cur_00177_cursor SCROLL CURSOR FOR SELECT id, payload FROM cur_00177_table ORDER BY id DESC;
FETCH PRIOR FROM cur_00177_cursor;
SELECT name, is_holdable, is_scrollable FROM pg_catalog.pg_cursors WHERE name = 'cur_00177_cursor' ORDER BY name;
CLOSE cur_00177_cursor;
SELECT id, payload FROM cur_00177_table ORDER BY id;
COMMIT;
DROP TABLE IF EXISTS cur_00177_table;
