# LargeSLB SQL Cases

每个 `TC-xxx.sql` 都是一个独立可执行 SQL 文件，文件头包含用例内容和预期结果。

执行示例：

```bash
mysql -h127.0.0.1 -P3306 -utest -ptest < TC-002.sql
```

当前内核 `innodb_log_write_max_size` 最大为 524288 字节，因此正向 LargeSLB 用例依赖多批 redo/GFB 在 slice flush session 中汇聚，而不是单次 redo write 达到 2MB。

并发、failover、CR、kill -9、磁盘满、网络断连、flush 失败等场景无法由单个 SQL 文件独立完成；对应 SQL 只提供负载入口，必须配合多客户端压测工具或故障注入框架执行完整场景。

注意：`TC-006.sql` 是不支持场景，单条 redo > 2MB 预期直接 crash，只能在隔离可丢弃实例中执行。

| 用例 | SQL 文件 | 过程 |
|------|----------|------|
| TC-001 | TC-001.sql | lgslb_tc001 |
| TC-002 | TC-002.sql | lgslb_tc002 |
| TC-003 | TC-003.sql | lgslb_tc003 |
| TC-004 | TC-004.sql | lgslb_tc004 |
| TC-005 | TC-005.sql | lgslb_tc005 |
| TC-006 | TC-006.sql | lgslb_tc006_unsupported_single_redo_crash |
| TC-007 | TC-007.sql | lgslb_tc007 |
| TC-008 | TC-008.sql | lgslb_tc008 |
| TC-009 | TC-009.sql | lgslb_tc009 |
| TC-010 | TC-010.sql | lgslb_tc010 |
| TC-011 | TC-011.sql | lgslb_tc011 |
| TC-012 | TC-012.sql | lgslb_tc012 |
| TC-013 | TC-013.sql | lgslb_tc013 |
| TC-014 | TC-014.sql | lgslb_tc014 |
| TC-015 | TC-015.sql | lgslb_tc015 |
| TC-016 | TC-016.sql | lgslb_tc016 |
| TC-017 | TC-017.sql | lgslb_tc017 |
| TC-018 | TC-018.sql | lgslb_tc018 |
| TC-019 | TC-019.sql | lgslb_tc019 |
| TC-020 | TC-020.sql | lgslb_tc020 |
| TC-021 | TC-021.sql | lgslb_tc021 |
| TC-022 | TC-022.sql | lgslb_tc022 |
| TC-023 | TC-023.sql | lgslb_tc023 |
| TC-024 | TC-024.sql | lgslb_tc024 |
| TC-025 | TC-025.sql | lgslb_tc025 |
| TC-026 | TC-026.sql | lgslb_tc026 |
| TC-027 | TC-027.sql | lgslb_tc027 |
| TC-028 | TC-028.sql | lgslb_tc028 |
| TC-029 | TC-029.sql | lgslb_tc029 |
| TC-030 | TC-030.sql | lgslb_tc030 |
