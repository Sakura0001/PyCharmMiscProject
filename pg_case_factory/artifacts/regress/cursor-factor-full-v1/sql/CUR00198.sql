-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 DECLARE with statement_branch=branch_1, expected_status=success, cursor_state=declared_open, direction_shape=forward_backward_count, hold_scroll_shape=no_scroll, cursor_name_shape=quoted_identifier, query_shape=ordered_select, transaction_context=inside_transaction, dependency_state=ready, invalid_combination=none, position_boundary=after_last, verification_mode=returned_rows, cleanup_mode=drop_objects
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=success
-- factor cursor_state=declared_open
-- factor direction_shape=forward_backward_count
-- factor hold_scroll_shape=no_scroll
-- factor cursor_name_shape=quoted_identifier
-- factor query_shape=ordered_select
-- factor transaction_context=inside_transaction
-- factor dependency_state=ready
-- factor invalid_combination=none
-- factor position_boundary=after_last
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS cur_00198_table;
CREATE TABLE cur_00198_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00198_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
BEGIN;
DECLARE "cur_00198_Cursor" NO SCROLL CURSOR FOR SELECT id, payload FROM cur_00198_table ORDER BY id DESC;
FETCH ABSOLUTE 999 FROM "cur_00198_Cursor";
SELECT name, is_holdable, is_scrollable FROM pg_catalog.pg_cursors WHERE name = '"cur_00198_Cursor"' ORDER BY name;
CLOSE "cur_00198_Cursor";
SELECT id, payload FROM cur_00198_table ORDER BY id;
COMMIT;
DROP TABLE IF EXISTS cur_00198_table;
