-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 CLOSE with statement_branch=branch_1, expected_status=failure, cursor_state=declared_open, direction_shape=relative, hold_scroll_shape=scroll, cursor_name_shape=all_cursors, query_shape=non_scrollable_query, transaction_context=inside_transaction, dependency_state=missing_dependency, invalid_combination=object_type_mismatch, position_boundary=negative_or_zero_count, verification_mode=catalog_query, cleanup_mode=reset_state
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor cursor_state=declared_open
-- factor direction_shape=relative
-- factor hold_scroll_shape=scroll
-- factor cursor_name_shape=all_cursors
-- factor query_shape=non_scrollable_query
-- factor transaction_context=inside_transaction
-- factor dependency_state=missing_dependency
-- factor invalid_combination=object_type_mismatch
-- factor position_boundary=negative_or_zero_count
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS cur_00067_table;
CREATE TABLE cur_00067_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00067_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
BEGIN;
DECLARE cur_00067_cursor SCROLL CURSOR FOR SELECT id FROM cur_00067_missing_table ORDER BY id;
CLOSE cur_00067_table;
SELECT name, is_holdable, is_scrollable FROM pg_catalog.pg_cursors ORDER BY name;
ROLLBACK;
RESET ALL;
DROP TABLE IF EXISTS cur_00067_table;
