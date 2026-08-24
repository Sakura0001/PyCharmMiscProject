-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 CLOSE with statement_branch=branch_1, expected_status=failure, cursor_state=declared_open, direction_shape=all, hold_scroll_shape=scroll, cursor_name_shape=missing_name, query_shape=simple_select, transaction_context=outside_transaction, dependency_state=ready, invalid_combination=syntax_valid_semantic_error, position_boundary=before_first, verification_mode=effect_query, cleanup_mode=drop_objects
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor cursor_state=declared_open
-- factor direction_shape=all
-- factor hold_scroll_shape=scroll
-- factor cursor_name_shape=missing_name
-- factor query_shape=simple_select
-- factor transaction_context=outside_transaction
-- factor dependency_state=ready
-- factor invalid_combination=syntax_valid_semantic_error
-- factor position_boundary=before_first
-- factor verification_mode=effect_query
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS cur_00072_table;
CREATE TABLE cur_00072_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00072_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
DECLARE cur_00072_cursor SCROLL CURSOR FOR SELECT id, payload FROM cur_00072_table ORDER BY id;
CLOSE cur_00072_missing_cursor;
SELECT count(*) AS cursor_effect_rows FROM cur_00072_table;
COMMIT;
DROP TABLE IF EXISTS cur_00072_table;
