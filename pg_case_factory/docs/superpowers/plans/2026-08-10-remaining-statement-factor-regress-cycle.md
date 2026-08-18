# 剩余语句 Regress 顺序生成计划

> 勾选项由进度状态生成，不手工修改。只有生成包通过校验并写入证据后才会勾选。

## 当前状态

- 清单指纹：`606b9e710210e50ff88b14de7052163f9ee31f6f1d1e744bc0bd9935f399a9d9`
- 下一条：`alter_function`

## 顺序清单

| 完成 | 序号 | 语句 | 分类目录 | 因子 / 值 | SQL 文件 | 生成包或状态 |
|---|---:|---|---|---:|---:|---|
| [x] | 001 | `abort` | `tcl/transaction` | 13 / 43 | 61 | `artifacts/regress/by-factor/tcl/transaction/abort` |
| [x] | 002 | `alter_aggregate` | `ddl/aggregate` | 20 / 52 | 783 | `artifacts/regress/by-factor/ddl/aggregate/alter_aggregate` |
| [x] | 003 | `alter_collation` | `ddl/collation` | 20 / 47 | 174 | `artifacts/regress/by-factor/ddl/collation/alter_collation` |
| [x] | 004 | `alter_conversion` | `ddl/conversion` | 24 / 62 | 216 | `artifacts/regress/by-factor/ddl/conversion/alter_conversion` |
| [x] | 005 | `alter_database` | `ddl/database` | 31 / 90 | 1420 | `artifacts/regress/by-factor/ddl/database/alter_database` |
| [x] | 006 | `alter_default_privileges` | `ddl/default_privileges` | 26 / 77 | 4271 | `artifacts/regress/by-factor/ddl/default_privileges/alter_default_privileges` |
| [x] | 007 | `alter_domain` | `ddl/domain` | 33 / 109 | 908 | `artifacts/regress/by-factor/ddl/domain/alter_domain` |
| [x] | 008 | `alter_event_trigger` | `ddl/event_trigger` | 20 / 56 | 159 | `artifacts/regress/by-factor/ddl/event_trigger/alter_event_trigger` |
| [x] | 009 | `alter_extension` | `ddl/extension` | 24 / 67 | 416 | `artifacts/regress/by-factor/ddl/extension/alter_extension` |
| [x] | 010 | `alter_foreign_data_wrapper` | `ddl/foreign_data_wrapper` | 26 / 67 | 155 | `artifacts/regress/by-factor/ddl/foreign_data_wrapper/alter_foreign_data_wrapper` |
| [x] | 011 | `alter_foreign_table` | `ddl/foreign_table` | 32 / 103 | 1805 | `artifacts/regress/by-factor/ddl/foreign_table/alter_foreign_table` |
| [ ] | 012 | `alter_function` | `ddl/function` | 24 / 85 | — | 待生成 |
| [ ] | 013 | `alter_group` | `ddl/group` | 23 / 57 | — | 待生成 |
| [ ] | 014 | `alter_index` | `ddl/index` | 19 / 66 | — | 待生成 |
| [ ] | 015 | `alter_language` | `ddl/language` | 14 / 38 | — | 待生成 |
| [ ] | 016 | `alter_large_object` | `ddl/large_object` | 11 / 28 | — | 待生成 |
| [ ] | 017 | `alter_materialized_view` | `ddl/materialized_view` | 15 / 53 | — | 待生成 |
| [ ] | 018 | `alter_operator` | `ddl/operator` | 17 / 54 | — | 待生成 |
| [ ] | 019 | `alter_operator_class` | `ddl/operator_class` | 15 / 46 | — | 待生成 |
| [ ] | 020 | `alter_operator_family` | `ddl/operator_family` | 16 / 52 | — | 待生成 |
| [ ] | 021 | `alter_policy` | `ddl/policy` | 24 / 68 | — | 待生成 |
| [ ] | 022 | `alter_procedure` | `ddl/procedure` | 24 / 70 | — | 待生成 |
| [ ] | 023 | `alter_publication` | `ddl/publication` | 24 / 65 | — | 待生成 |
| [ ] | 024 | `alter_role` | `ddl/role` | 23 / 98 | — | 待生成 |
| [ ] | 025 | `alter_routine` | `ddl/routine` | 23 / 80 | — | 待生成 |
| [ ] | 026 | `alter_rule` | `ddl/rule` | 17 / 43 | — | 待生成 |
| [ ] | 027 | `alter_schema` | `ddl/schema` | 21 / 53 | — | 待生成 |
| [ ] | 028 | `alter_sequence` | `ddl/sequence` | 25 / 69 | — | 待生成 |
| [ ] | 029 | `alter_server` | `ddl/server` | 20 / 48 | — | 待生成 |
| [ ] | 030 | `alter_statistics` | `ddl/statistics` | 22 / 50 | — | 待生成 |
| [ ] | 031 | `alter_subscription` | `ddl/subscription` | 26 / 70 | — | 待生成 |
| [ ] | 032 | `alter_system` | `ddl/system` | 18 / 49 | — | 待生成 |
| [ ] | 033 | `alter_table` | `ddl/table` | 35 / 197 | — | 待生成 |
| [ ] | 034 | `alter_tablespace` | `ddl/tablespace` | 23 / 68 | — | 待生成 |
| [ ] | 035 | `alter_text_search_configuration` | `ddl/text_search_configuration` | 28 / 81 | — | 待生成 |
| [ ] | 036 | `alter_text_search_dictionary` | `ddl/text_search_dictionary` | 22 / 60 | — | 待生成 |
| [ ] | 037 | `alter_text_search_parser` | `ddl/text_search_parser` | 15 / 33 | — | 待生成 |
| [ ] | 038 | `alter_text_search_template` | `ddl/text_search_template` | 15 / 33 | — | 待生成 |
| [ ] | 039 | `alter_trigger` | `ddl/trigger` | 19 / 41 | — | 待生成 |
| [ ] | 040 | `alter_type` | `ddl/type` | 30 / 84 | — | 待生成 |
| [ ] | 041 | `alter_user` | `ddl/user` | 20 / 69 | — | 待生成 |
| [ ] | 042 | `alter_user_mapping` | `ddl/user_mapping` | 20 / 54 | — | 待生成 |
| [ ] | 043 | `alter_view` | `ddl/view` | 15 / 63 | — | 待生成 |
| [ ] | 044 | `analyze` | `utility/statistics` | 13 / 47 | — | 待生成 |
| [ ] | 045 | `begin` | `tcl/transaction` | 13 / 43 | — | 待生成 |
| [ ] | 046 | `call` | `dml/routine` | 15 / 48 | — | 待生成 |
| [ ] | 047 | `checkpoint` | `utility/checkpoint` | 13 / 45 | — | 待生成 |
| [x] | 048 | `close` | `cursor/cursor` | 13 / 45 | — | `artifacts/regress/cursor-factor-full-v1`（保留已有） |
| [ ] | 049 | `cluster` | `ddl/table` | 18 / 55 | — | 待生成 |
| [ ] | 050 | `comment` | `ddl/comment` | 26 / 117 | — | 待生成 |
| [ ] | 051 | `commit` | `tcl/transaction` | 13 / 43 | — | 待生成 |
| [ ] | 052 | `commit_prepared` | `tcl/two_phase_transaction` | 13 / 43 | — | 待生成 |
| [ ] | 053 | `copy` | `utility/data_transfer` | 13 / 49 | — | 待生成 |
| [ ] | 054 | `create_access_method` | `ddl/access_method` | 15 / 30 | — | 待生成 |
| [ ] | 055 | `create_aggregate` | `ddl/aggregate` | 23 / 66 | — | 待生成 |
| [ ] | 056 | `create_cast` | `ddl/cast` | 20 / 60 | — | 待生成 |
| [ ] | 057 | `create_collation` | `ddl/collation` | 23 / 50 | — | 待生成 |
| [ ] | 058 | `create_conversion` | `ddl/conversion` | 23 / 64 | — | 待生成 |
| [ ] | 059 | `create_database` | `ddl/database` | 27 / 67 | — | 待生成 |
| [ ] | 060 | `create_domain` | `ddl/domain` | 28 / 96 | — | 待生成 |
| [ ] | 061 | `create_event_trigger` | `ddl/event_trigger` | 24 / 61 | — | 待生成 |
| [ ] | 062 | `create_extension` | `ddl/extension` | 24 / 62 | — | 待生成 |
| [ ] | 063 | `create_foreign_data_wrapper` | `ddl/foreign_data_wrapper` | 24 / 57 | — | 待生成 |
| [ ] | 064 | `create_foreign_table` | `ddl/foreign_table` | 32 / 91 | — | 待生成 |
| [ ] | 065 | `create_function` | `ddl/function` | 34 / 121 | — | 待生成 |
| [ ] | 066 | `create_group` | `ddl/group` | 25 / 64 | — | 待生成 |
| [ ] | 067 | `create_index` | `ddl/index` | 26 / 89 | — | 待生成 |
| [ ] | 068 | `create_language` | `ddl/language` | 17 / 42 | — | 待生成 |
| [ ] | 069 | `create_materialized_view` | `ddl/materialized_view` | 19 / 47 | — | 待生成 |
| [ ] | 070 | `create_operator` | `ddl/operator` | 23 / 55 | — | 待生成 |
| [ ] | 071 | `create_operator_class` | `ddl/operator_class` | 18 / 53 | — | 待生成 |
| [ ] | 072 | `create_operator_family` | `ddl/operator_family` | 11 / 30 | — | 待生成 |
| [ ] | 073 | `create_policy` | `ddl/policy` | 26 / 80 | — | 待生成 |
| [ ] | 074 | `create_procedure` | `ddl/procedure` | 26 / 92 | — | 待生成 |
| [ ] | 075 | `create_publication` | `ddl/publication` | 23 / 68 | — | 待生成 |
| [ ] | 076 | `create_role` | `ddl/role` | 22 / 101 | — | 待生成 |
| [ ] | 077 | `create_rule` | `ddl/rule` | 24 / 72 | — | 待生成 |
| [ ] | 078 | `create_schema` | `ddl/schema` | 20 / 58 | — | 待生成 |
| [ ] | 079 | `create_sequence` | `ddl/sequence` | 28 / 70 | — | 待生成 |
| [ ] | 080 | `create_server` | `ddl/server` | 18 / 41 | — | 待生成 |
| [ ] | 081 | `create_statistics` | `ddl/statistics` | 22 / 54 | — | 待生成 |
| [ ] | 082 | `create_subscription` | `ddl/subscription` | 21 / 54 | — | 待生成 |
| [ ] | 083 | `create_table` | `ddl/table` | 38 / 185 | — | 待生成 |
| [ ] | 084 | `create_table_as` | `ddl/table` | 26 / 83 | — | 待生成 |
| [ ] | 085 | `create_tablespace` | `ddl/tablespace` | 24 / 66 | — | 待生成 |
| [ ] | 086 | `create_text_search_configuration` | `ddl/text_search_configuration` | 21 / 52 | — | 待生成 |
| [ ] | 087 | `create_text_search_dictionary` | `ddl/text_search_dictionary` | 18 / 44 | — | 待生成 |
| [ ] | 088 | `create_text_search_parser` | `ddl/text_search_parser` | 16 / 37 | — | 待生成 |
| [ ] | 089 | `create_text_search_template` | `ddl/text_search_template` | 16 / 37 | — | 待生成 |
| [ ] | 090 | `create_transform` | `ddl/transform` | 26 / 58 | — | 待生成 |
| [ ] | 091 | `create_trigger` | `ddl/trigger` | 34 / 88 | — | 待生成 |
| [ ] | 092 | `create_type` | `ddl/type` | 32 / 91 | — | 待生成 |
| [ ] | 093 | `create_user` | `ddl/user` | 19 / 53 | — | 待生成 |
| [ ] | 094 | `create_user_mapping` | `ddl/user_mapping` | 18 / 45 | — | 待生成 |
| [ ] | 095 | `create_view` | `ddl/view` | 18 / 70 | — | 待生成 |
| [ ] | 096 | `deallocate` | `prepared/prepared_statement` | 13 / 41 | — | 待生成 |
| [x] | 097 | `declare` | `cursor/cursor` | 13 / 45 | — | `artifacts/regress/cursor-factor-full-v1`（保留已有） |
| [ ] | 098 | `delete` | `dml/table` | 15 / 49 | — | 待生成 |
| [ ] | 099 | `discard` | `session/session_state` | 13 / 41 | — | 待生成 |
| [ ] | 100 | `do` | `utility/anonymous_code` | 13 / 45 | — | 待生成 |
| [ ] | 101 | `drop_access_method` | `ddl/access_method` | 13 / 28 | — | 待生成 |
| [ ] | 102 | `drop_aggregate` | `ddl/aggregate` | 17 / 37 | — | 待生成 |
| [ ] | 103 | `drop_cast` | `ddl/cast` | 16 / 41 | — | 待生成 |
| [ ] | 104 | `drop_collation` | `ddl/collation` | 13 / 27 | — | 待生成 |
| [ ] | 105 | `drop_conversion` | `ddl/conversion` | 15 / 35 | — | 待生成 |
| [ ] | 106 | `drop_database` | `ddl/database` | 21 / 47 | — | 待生成 |
| [ ] | 107 | `drop_domain` | `ddl/domain` | 15 / 42 | — | 待生成 |
| [ ] | 108 | `drop_event_trigger` | `ddl/event_trigger` | 15 / 35 | — | 待生成 |
| [ ] | 109 | `drop_extension` | `ddl/extension` | 17 / 42 | — | 待生成 |
| [ ] | 110 | `drop_foreign_data_wrapper` | `ddl/foreign_data_wrapper` | 17 / 42 | — | 待生成 |
| [ ] | 111 | `drop_foreign_table` | `ddl/foreign_table` | 16 / 41 | — | 待生成 |
| [ ] | 112 | `drop_function` | `ddl/function` | 18 / 42 | — | 待生成 |
| [ ] | 113 | `drop_group` | `ddl/group` | 19 / 41 | — | 待生成 |
| [ ] | 114 | `drop_index` | `ddl/index` | 16 / 53 | — | 待生成 |
| [ ] | 115 | `drop_language` | `ddl/language` | 13 / 32 | — | 待生成 |
| [ ] | 116 | `drop_materialized_view` | `ddl/materialized_view` | 13 / 34 | — | 待生成 |
| [ ] | 117 | `drop_operator` | `ddl/operator` | 16 / 40 | — | 待生成 |
| [ ] | 118 | `drop_operator_class` | `ddl/operator_class` | 16 / 43 | — | 待生成 |
| [ ] | 119 | `drop_operator_family` | `ddl/operator_family` | 15 / 42 | — | 待生成 |
| [ ] | 120 | `drop_owned` | `ddl/ownership` | 15 / 41 | — | 待生成 |
| [ ] | 121 | `drop_policy` | `ddl/policy` | 17 / 45 | — | 待生成 |
| [ ] | 122 | `drop_procedure` | `ddl/procedure` | 18 / 40 | — | 待生成 |
| [ ] | 123 | `drop_publication` | `ddl/publication` | 15 / 37 | — | 待生成 |
| [ ] | 124 | `drop_role` | `ddl/role` | 15 / 56 | — | 待生成 |
| [ ] | 125 | `drop_routine` | `ddl/routine` | 20 / 60 | — | 待生成 |
| [ ] | 126 | `drop_rule` | `ddl/rule` | 18 / 47 | — | 待生成 |
| [ ] | 127 | `drop_schema` | `ddl/schema` | 13 / 40 | — | 待生成 |
| [ ] | 128 | `drop_sequence` | `ddl/sequence` | 13 / 43 | — | 待生成 |
| [ ] | 129 | `drop_server` | `ddl/server` | 15 / 36 | — | 待生成 |
| [ ] | 130 | `drop_statistics` | `ddl/statistics` | 13 / 32 | — | 待生成 |
| [ ] | 131 | `drop_subscription` | `ddl/subscription` | 15 / 33 | — | 待生成 |
| [ ] | 132 | `drop_table` | `ddl/table` | 13 / 47 | — | 待生成 |
| [ ] | 133 | `drop_tablespace` | `ddl/tablespace` | 13 / 42 | — | 待生成 |
| [ ] | 134 | `drop_text_search_configuration` | `ddl/text_search_configuration` | 13 / 35 | — | 待生成 |
| [ ] | 135 | `drop_text_search_dictionary` | `ddl/text_search_dictionary` | 13 / 35 | — | 待生成 |
| [ ] | 136 | `drop_text_search_parser` | `ddl/text_search_parser` | 13 / 33 | — | 待生成 |
| [ ] | 137 | `drop_text_search_template` | `ddl/text_search_template` | 13 / 33 | — | 待生成 |
| [ ] | 138 | `drop_transform` | `ddl/transform` | 20 / 45 | — | 待生成 |
| [ ] | 139 | `drop_trigger` | `ddl/trigger` | 16 / 33 | — | 待生成 |
| [ ] | 140 | `drop_type` | `ddl/type` | 13 / 43 | — | 待生成 |
| [ ] | 141 | `drop_user` | `ddl/user` | 13 / 36 | — | 待生成 |
| [ ] | 142 | `drop_user_mapping` | `ddl/user_mapping` | 17 / 43 | — | 待生成 |
| [ ] | 143 | `drop_view` | `ddl/view` | 12 / 37 | — | 待生成 |
| [ ] | 144 | `end` | `tcl/transaction` | 13 / 43 | — | 待生成 |
| [ ] | 145 | `execute` | `prepared/prepared_statement` | 13 / 41 | — | 待生成 |
| [ ] | 146 | `explain` | `utility/plan` | 13 / 47 | — | 待生成 |
| [x] | 147 | `fetch` | `cursor/cursor` | 13 / 45 | — | `artifacts/regress/cursor-factor-full-v1`（保留已有） |
| [x] | 148 | `grant` | `dcl/privilege` | 14 / 61 | — | `artifacts/regress/dcl-factor-full-v1`（保留已有） |
| [ ] | 149 | `import_foreign_schema` | `ddl/foreign_schema` | 24 / 56 | — | 待生成 |
| [ ] | 150 | `insert` | `dml/table` | 15 / 49 | — | 待生成 |
| [ ] | 151 | `listen` | `session/notification` | 13 / 41 | — | 待生成 |
| [ ] | 152 | `load` | `utility/library` | 13 / 45 | — | 待生成 |
| [ ] | 153 | `lock` | `utility/lock` | 13 / 46 | — | 待生成 |
| [ ] | 154 | `merge` | `dml/table` | 15 / 51 | — | 待生成 |
| [x] | 155 | `move` | `cursor/cursor` | 13 / 45 | — | `artifacts/regress/cursor-factor-full-v1`（保留已有） |
| [ ] | 156 | `notify` | `session/notification` | 13 / 41 | — | 待生成 |
| [ ] | 157 | `prepare` | `prepared/prepared_statement` | 13 / 41 | — | 待生成 |
| [ ] | 158 | `prepare_transaction` | `tcl/two_phase_transaction` | 13 / 43 | — | 待生成 |
| [ ] | 159 | `reassign_owned` | `ddl/ownership` | 18 / 46 | — | 待生成 |
| [ ] | 160 | `refresh_materialized_view` | `ddl/materialized_view` | 14 / 38 | — | 待生成 |
| [ ] | 161 | `reindex` | `ddl/index` | 20 / 83 | — | 待生成 |
| [ ] | 162 | `release_savepoint` | `tcl/savepoint` | 13 / 43 | — | 待生成 |
| [ ] | 163 | `reset` | `session/runtime_parameter` | 13 / 41 | — | 待生成 |
| [x] | 164 | `revoke` | `dcl/privilege` | 14 / 61 | — | `artifacts/regress/dcl-factor-full-v1`（保留已有） |
| [ ] | 165 | `rollback` | `tcl/transaction` | 13 / 43 | — | 待生成 |
| [ ] | 166 | `rollback_prepared` | `tcl/two_phase_transaction` | 13 / 43 | — | 待生成 |
| [ ] | 167 | `rollback_to_savepoint` | `tcl/savepoint` | 13 / 43 | — | 待生成 |
| [ ] | 168 | `savepoint` | `tcl/savepoint` | 13 / 43 | — | 待生成 |
| [ ] | 169 | `security_label` | `ddl/security_label` | 22 / 86 | — | 待生成 |
| [ ] | 170 | `select` | `dml/query` | 15 / 50 | — | 待生成 |
| [ ] | 171 | `select_into` | `ddl/table` | 23 / 56 | — | 待生成 |
| [ ] | 172 | `set` | `session/runtime_parameter` | 13 / 43 | — | 待生成 |
| [ ] | 173 | `set_constraints` | `session/constraint_mode` | 13 / 41 | — | 待生成 |
| [ ] | 174 | `set_role` | `session/authorization` | 13 / 42 | — | 待生成 |
| [ ] | 175 | `set_session_authorization` | `session/authorization` | 13 / 41 | — | 待生成 |
| [ ] | 176 | `set_transaction` | `tcl/transaction` | 13 / 43 | — | 待生成 |
| [ ] | 177 | `show` | `session/runtime_parameter` | 13 / 43 | — | 待生成 |
| [ ] | 178 | `start_transaction` | `tcl/transaction` | 13 / 43 | — | 待生成 |
| [ ] | 179 | `truncate` | `ddl/table` | 17 / 52 | — | 待生成 |
| [ ] | 180 | `unlisten` | `session/notification` | 13 / 41 | — | 待生成 |
| [ ] | 181 | `update` | `dml/table` | 15 / 49 | — | 待生成 |
| [ ] | 182 | `vacuum` | `utility/maintenance` | 13 / 47 | — | 待生成 |
| [ ] | 183 | `values` | `dml/query` | 15 / 48 | — | 待生成 |
