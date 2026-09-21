-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 内网环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: BINARY + VARBINARY + DECIMAL + TEXT + BLOB + BIT
-- 覆盖算法: INSTANT + INPLACE (增强类型 INSTANT 预期成功 (BINARY/VARBINARY/DECIMAL 已确认支持))
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- 生成时间: 2026-09-20
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

-- File 16: BINARY INSTANT (预期成功)

-- Test Case: TC-I0001
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0001, t2_i0001;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0001 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0001 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0001 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0001 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0001 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0001 (target) VALUES ('');
INSERT INTO t1_i0001 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0001 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0001 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0001 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0001 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0001 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0001 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0001 (target) VALUES ('');
INSERT INTO t1_i0001 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0001 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0001 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0001 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0001 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0001 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0001 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0001 (target) VALUES ('');
INSERT INTO t2_i0001 (target) VALUES (NULL);
INSERT INTO t2_i0001 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0001 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0001 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0001 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0001 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0001 (target) VALUES ('');
INSERT INTO t2_i0001 (target) VALUES (NULL);
SELECT 'TC-I0001' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0001
   WHERE id NOT IN (SELECT id FROM t2_i0001)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0001
   WHERE id NOT IN (SELECT id FROM t1_i0001)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0001 a JOIN t2_i0001 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0002
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0002, t2_i0002;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0002 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t1_i0002 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0002 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0002 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0002 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0002 (target) VALUES ('');
INSERT INTO t1_i0002 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0002 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0002 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0002 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0002 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0002 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0002 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0002 (target) VALUES ('');
INSERT INTO t1_i0002 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0002 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0002 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t2_i0002 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0002 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0002 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0002 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0002 (target) VALUES ('');
INSERT INTO t2_i0002 (target) VALUES (NULL);
INSERT INTO t2_i0002 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0002 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0002 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0002 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0002 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0002 (target) VALUES ('');
INSERT INTO t2_i0002 (target) VALUES (NULL);
SELECT 'TC-I0002' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0002
   WHERE id NOT IN (SELECT id FROM t2_i0002)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0002
   WHERE id NOT IN (SELECT id FROM t1_i0002)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0002 a JOIN t2_i0002 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0003
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0003, t2_i0003;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0003 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t1_i0003 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0003 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0003 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0003 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0003 (target) VALUES ('');
INSERT INTO t1_i0003 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0003 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0003 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0003 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0003 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0003 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0003 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0003 (target) VALUES ('');
INSERT INTO t1_i0003 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0003 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0003 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t2_i0003 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0003 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0003 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0003 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0003 (target) VALUES ('');
INSERT INTO t2_i0003 (target) VALUES (NULL);
INSERT INTO t2_i0003 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0003 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0003 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0003 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0003 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0003 (target) VALUES ('');
INSERT INTO t2_i0003 (target) VALUES (NULL);
SELECT 'TC-I0003' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0003
   WHERE id NOT IN (SELECT id FROM t2_i0003)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0003
   WHERE id NOT IN (SELECT id FROM t1_i0003)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0003 a JOIN t2_i0003 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0004
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0004, t2_i0004;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0004 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0004 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0004 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0004 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0004 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0004 (target) VALUES ('');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_i0004 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0004 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0004 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0004 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0004 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0004 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0004 (target) VALUES ('');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0004 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(10)
CREATE TABLE t2_i0004 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0004 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0004 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0004 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0004 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0004 (target) VALUES ('');
INSERT INTO t2_i0004 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0004 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0004 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0004 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0004 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0004 (target) VALUES ('');
SELECT 'TC-I0004' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0004
   WHERE id NOT IN (SELECT id FROM t2_i0004)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0004
   WHERE id NOT IN (SELECT id FROM t1_i0004)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0004 a JOIN t2_i0004 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0005
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0005, t2_i0005;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0005 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0005 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0005 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0005 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0005 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0005 (target) VALUES ('');
INSERT INTO t1_i0005 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0005 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0005 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0005 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0005 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0005 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0005 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0005 (target) VALUES ('');
INSERT INTO t1_i0005 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0005 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0005 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0005 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0005 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0005 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0005 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0005 (target) VALUES ('');
INSERT INTO t2_i0005 (target) VALUES (NULL);
INSERT INTO t2_i0005 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0005 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0005 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0005 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0005 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0005 (target) VALUES ('');
INSERT INTO t2_i0005 (target) VALUES (NULL);
SELECT 'TC-I0005' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0005
   WHERE id NOT IN (SELECT id FROM t2_i0005)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0005
   WHERE id NOT IN (SELECT id FROM t1_i0005)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0005 a JOIN t2_i0005 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0006
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0006, t2_i0006;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0006 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0006 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0006 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0006 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0006 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0006 (target) VALUES ('');
INSERT INTO t1_i0006 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0006 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0006 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0006 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0006 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0006 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0006 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0006 (target) VALUES ('');
INSERT INTO t1_i0006 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0006 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0006 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0006 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0006 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0006 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0006 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0006 (target) VALUES ('');
INSERT INTO t2_i0006 (target) VALUES (NULL);
INSERT INTO t2_i0006 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0006 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0006 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0006 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0006 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0006 (target) VALUES ('');
INSERT INTO t2_i0006 (target) VALUES (NULL);
SELECT 'TC-I0006' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0006
   WHERE id NOT IN (SELECT id FROM t2_i0006)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0006
   WHERE id NOT IN (SELECT id FROM t1_i0006)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0006 a JOIN t2_i0006 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0007
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0007, t2_i0007;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0007 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0007 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0007 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0007 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0007 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0007 (target) VALUES ('');
INSERT INTO t1_i0007 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0007 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0007 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0007 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0007 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0007 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0007 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0007 (target) VALUES ('');
INSERT INTO t1_i0007 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0007 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0007 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0007 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0007 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0007 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0007 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0007 (target) VALUES ('');
INSERT INTO t2_i0007 (target) VALUES (NULL);
INSERT INTO t2_i0007 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0007 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0007 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0007 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0007 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0007 (target) VALUES ('');
INSERT INTO t2_i0007 (target) VALUES (NULL);
SELECT 'TC-I0007' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0007
   WHERE id NOT IN (SELECT id FROM t2_i0007)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0007
   WHERE id NOT IN (SELECT id FROM t1_i0007)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0007 a JOIN t2_i0007 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0008
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0008, t2_i0008;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0008 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0008 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0008 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0008 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0008 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0008 (target) VALUES ('');
INSERT INTO t1_i0008 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0008 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0008 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0008 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0008 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0008 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0008 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0008 (target) VALUES ('');
INSERT INTO t1_i0008 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0008 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0008 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0008 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0008 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0008 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0008 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0008 (target) VALUES ('');
INSERT INTO t2_i0008 (target) VALUES (NULL);
INSERT INTO t2_i0008 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0008 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0008 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0008 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0008 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0008 (target) VALUES ('');
INSERT INTO t2_i0008 (target) VALUES (NULL);
SELECT 'TC-I0008' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0008
   WHERE id NOT IN (SELECT id FROM t2_i0008)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0008
   WHERE id NOT IN (SELECT id FROM t1_i0008)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0008 a JOIN t2_i0008 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0009
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0009, t2_i0009;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0009 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0009 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0009 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0009 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0009 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0009 (target) VALUES ('');
INSERT INTO t1_i0009 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0009 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0009 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0009 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0009 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0009 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0009 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0009 (target) VALUES ('');
INSERT INTO t1_i0009 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0009 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0009 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0009 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0009 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0009 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0009 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0009 (target) VALUES ('');
INSERT INTO t2_i0009 (target) VALUES (NULL);
INSERT INTO t2_i0009 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0009 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0009 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0009 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0009 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0009 (target) VALUES ('');
INSERT INTO t2_i0009 (target) VALUES (NULL);
SELECT 'TC-I0009' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0009
   WHERE id NOT IN (SELECT id FROM t2_i0009)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0009
   WHERE id NOT IN (SELECT id FROM t1_i0009)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0009 a JOIN t2_i0009 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0010
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_i0010, t2_i0010;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0010 (
  target BINARY(10),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0010 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0010 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0010 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0010 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0010 (target) VALUES ('');
INSERT INTO t1_i0010 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0010 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0010 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0010 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0010 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0010 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0010 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0010 (target) VALUES ('');
INSERT INTO t1_i0010 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0010 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0010 (
  target BINARY(20),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0010 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0010 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0010 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0010 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0010 (target) VALUES ('');
INSERT INTO t2_i0010 (target) VALUES (NULL);
INSERT INTO t2_i0010 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0010 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0010 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0010 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0010 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0010 (target) VALUES ('');
INSERT INTO t2_i0010 (target) VALUES (NULL);
SELECT 'TC-I0010' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0010
   WHERE id NOT IN (SELECT id FROM t2_i0010)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0010
   WHERE id NOT IN (SELECT id FROM t1_i0010)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0010 a JOIN t2_i0010 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0011
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_i0011, t2_i0011;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0011 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target BINARY(10), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0011 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0011 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0011 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0011 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0011 (target) VALUES ('');
INSERT INTO t1_i0011 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0011 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0011 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0011 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0011 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0011 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0011 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0011 (target) VALUES ('');
INSERT INTO t1_i0011 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0011 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0011 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target BINARY(20), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0011 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0011 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0011 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0011 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0011 (target) VALUES ('');
INSERT INTO t2_i0011 (target) VALUES (NULL);
INSERT INTO t2_i0011 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0011 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0011 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0011 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0011 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0011 (target) VALUES ('');
INSERT INTO t2_i0011 (target) VALUES (NULL);
SELECT 'TC-I0011' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0011
   WHERE id NOT IN (SELECT id FROM t2_i0011)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0011
   WHERE id NOT IN (SELECT id FROM t1_i0011)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0011 a JOIN t2_i0011 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0012
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0012, t2_i0012;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0012 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0012 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0012 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0012 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0012 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0012 (target) VALUES ('');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0012 MODIFY target BINARY(20) NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0012 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0012 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0012 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0012 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0012 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0012 (target) VALUES ('');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0012 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0012 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0012 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0012 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0012 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0012 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0012 (target) VALUES ('');
INSERT INTO t2_i0012 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0012 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0012 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0012 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0012 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0012 (target) VALUES ('');
SELECT 'TC-I0012' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0012
   WHERE id NOT IN (SELECT id FROM t2_i0012)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0012
   WHERE id NOT IN (SELECT id FROM t1_i0012)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0012 a JOIN t2_i0012 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0013
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0013, t2_i0013;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0013 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10) DEFAULT 0x00,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0013 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0013 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0013 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0013 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0013 (target) VALUES ('');
INSERT INTO t1_i0013 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0013 MODIFY target BINARY(20) DEFAULT 0x00, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0013 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0013 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0013 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0013 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0013 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0013 (target) VALUES ('');
INSERT INTO t1_i0013 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0013 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0013 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20) DEFAULT 0x00,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0013 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0013 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0013 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0013 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0013 (target) VALUES ('');
INSERT INTO t2_i0013 (target) VALUES (NULL);
INSERT INTO t2_i0013 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0013 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0013 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0013 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0013 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0013 (target) VALUES ('');
INSERT INTO t2_i0013 (target) VALUES (NULL);
SELECT 'TC-I0013' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0013
   WHERE id NOT IN (SELECT id FROM t2_i0013)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0013
   WHERE id NOT IN (SELECT id FROM t1_i0013)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0013 a JOIN t2_i0013 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0014
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0014, t2_i0014;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0014 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0014 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0014 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0014 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0014 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0014 (target) VALUES ('');
INSERT INTO t1_i0014 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0014 MODIFY target BINARY(20) DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0014 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0014 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0014 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0014 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0014 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0014 (target) VALUES ('');
INSERT INTO t1_i0014 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0014 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0014 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0014 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0014 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0014 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0014 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0014 (target) VALUES ('');
INSERT INTO t2_i0014 (target) VALUES (NULL);
INSERT INTO t2_i0014 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0014 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0014 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0014 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0014 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0014 (target) VALUES ('');
INSERT INTO t2_i0014 (target) VALUES (NULL);
SELECT 'TC-I0014' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0014
   WHERE id NOT IN (SELECT id FROM t2_i0014)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0014
   WHERE id NOT IN (SELECT id FROM t1_i0014)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0014 a JOIN t2_i0014 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0015
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0015, t2_i0015;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0015 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10) NOT NULL DEFAULT 0x00,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0015 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0015 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0015 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0015 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0015 (target) VALUES ('');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0015 MODIFY target BINARY(20) NOT NULL DEFAULT 0x00, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0015 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0015 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0015 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0015 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0015 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0015 (target) VALUES ('');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0015 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0015 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20) NOT NULL DEFAULT 0x00,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0015 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0015 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0015 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0015 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0015 (target) VALUES ('');
INSERT INTO t2_i0015 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0015 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0015 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0015 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0015 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0015 (target) VALUES ('');
SELECT 'TC-I0015' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0015
   WHERE id NOT IN (SELECT id FROM t2_i0015)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0015
   WHERE id NOT IN (SELECT id FROM t1_i0015)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0015 a JOIN t2_i0015 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0016
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0016, t2_i0016;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0016 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0016 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0016 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0016 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0016 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0016 (target) VALUES ('');
INSERT INTO t1_i0016 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0016 MODIFY target BINARY(20) INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0016 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0016 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0016 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0016 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0016 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0016 (target) VALUES ('');
INSERT INTO t1_i0016 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0016 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0016 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0016 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0016 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0016 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0016 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0016 (target) VALUES ('');
INSERT INTO t2_i0016 (target) VALUES (NULL);
INSERT INTO t2_i0016 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0016 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0016 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0016 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0016 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0016 (target) VALUES ('');
INSERT INTO t2_i0016 (target) VALUES (NULL);
SELECT 'TC-I0016' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0016
   WHERE id NOT IN (SELECT id FROM t2_i0016)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0016
   WHERE id NOT IN (SELECT id FROM t1_i0016)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0016 a JOIN t2_i0016 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0017
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0017, t2_i0017;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0017 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0017 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0017 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0017 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0017' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0017
   WHERE id NOT IN (SELECT id FROM t2_i0017)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0017
   WHERE id NOT IN (SELECT id FROM t1_i0017)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0017 a JOIN t2_i0017 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0018
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0018, t2_i0018;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0018 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0018 (target) VALUES (0x00000000000000000000);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0018 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0018 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0018 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0018 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0018 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0018 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0018 (target) VALUES ('');
INSERT INTO t1_i0018 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0018 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0018 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0018 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0018 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0018 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0018 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0018 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0018 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0018 (target) VALUES ('');
INSERT INTO t2_i0018 (target) VALUES (NULL);
SELECT 'TC-I0018' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0018
   WHERE id NOT IN (SELECT id FROM t2_i0018)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0018
   WHERE id NOT IN (SELECT id FROM t1_i0018)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0018 a JOIN t2_i0018 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0019
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0019, t2_i0019;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0019 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0019 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0019 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0019 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0019 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0019 (target) VALUES ('');
INSERT INTO t1_i0019 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0019 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0019 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0019 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0019 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0019 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0019 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0019 (target) VALUES ('');
INSERT INTO t1_i0019 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0019 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0019 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0019 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0019 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0019 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0019 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0019 (target) VALUES ('');
INSERT INTO t2_i0019 (target) VALUES (NULL);
INSERT INTO t2_i0019 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0019 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0019 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0019 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0019 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0019 (target) VALUES ('');
INSERT INTO t2_i0019 (target) VALUES (NULL);
SELECT 'TC-I0019' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0019
   WHERE id NOT IN (SELECT id FROM t2_i0019)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0019
   WHERE id NOT IN (SELECT id FROM t1_i0019)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0019 a JOIN t2_i0019 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0020
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0020, t2_i0020;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0020 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0020 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0020 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0020 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0020 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0020 (target) VALUES ('');
INSERT INTO t1_i0020 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0020 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0020 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0020 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0020 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0020 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0020 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0020 (target) VALUES ('');
INSERT INTO t1_i0020 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0020 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0020 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0020 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0020 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0020 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0020 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0020 (target) VALUES ('');
INSERT INTO t2_i0020 (target) VALUES (NULL);
INSERT INTO t2_i0020 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0020 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0020 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0020 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0020 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0020 (target) VALUES ('');
INSERT INTO t2_i0020 (target) VALUES (NULL);
SELECT 'TC-I0020' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0020
   WHERE id NOT IN (SELECT id FROM t2_i0020)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0020
   WHERE id NOT IN (SELECT id FROM t1_i0020)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0020 a JOIN t2_i0020 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0021
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0021, t2_i0021;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0021 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0021 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0021 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0021 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0021 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0021 (target) VALUES ('');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0021 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0021 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0021 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0021 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0021 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0021 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0021 (target) VALUES ('');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0021 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0021 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0021 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0021 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0021 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0021 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0021 (target) VALUES ('');
INSERT INTO t2_i0021 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0021 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0021 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0021 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0021 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0021 (target) VALUES ('');
SELECT 'TC-I0021' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0021
   WHERE id NOT IN (SELECT id FROM t2_i0021)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0021
   WHERE id NOT IN (SELECT id FROM t1_i0021)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0021 a JOIN t2_i0021 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0022
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0022, t2_i0022;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0022 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0022 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0022 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0022 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0022 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0022 (target) VALUES ('');
INSERT INTO t1_i0022 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0022 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0022 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0022 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0022 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0022 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0022 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0022 (target) VALUES ('');
INSERT INTO t1_i0022 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0022 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0022 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0022 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0022 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0022 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0022 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0022 (target) VALUES ('');
INSERT INTO t2_i0022 (target) VALUES (NULL);
INSERT INTO t2_i0022 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0022 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0022 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0022 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0022 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0022 (target) VALUES ('');
INSERT INTO t2_i0022 (target) VALUES (NULL);
SELECT 'TC-I0022' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0022
   WHERE id NOT IN (SELECT id FROM t2_i0022)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0022
   WHERE id NOT IN (SELECT id FROM t1_i0022)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0022 a JOIN t2_i0022 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0023
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0023, t2_i0023;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0023 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0023 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0023 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0023 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0023 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0023 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0023 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0023 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0023 (target) VALUES ('');
INSERT INTO t1_i0023 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0023 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0023 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0023 (target) VALUES (NULL);
INSERT INTO t2_i0023 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0023 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0023 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0023 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0023 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0023 (target) VALUES ('');
INSERT INTO t2_i0023 (target) VALUES (NULL);
SELECT 'TC-I0023' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0023
   WHERE id NOT IN (SELECT id FROM t2_i0023)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0023
   WHERE id NOT IN (SELECT id FROM t1_i0023)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0023 a JOIN t2_i0023 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0024
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0024, t2_i0024;
SET SESSION sql_mode = '';
CREATE TABLE t1_i0024 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0024 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0024 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0024 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0024 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0024 (target) VALUES ('');
INSERT INTO t1_i0024 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0024 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0024 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0024 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0024 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0024 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0024 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0024 (target) VALUES ('');
INSERT INTO t1_i0024 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0024 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0024 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0024 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0024 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0024 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0024 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0024 (target) VALUES ('');
INSERT INTO t2_i0024 (target) VALUES (NULL);
INSERT INTO t2_i0024 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0024 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0024 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0024 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0024 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0024 (target) VALUES ('');
INSERT INTO t2_i0024 (target) VALUES (NULL);
SELECT 'TC-I0024' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0024
   WHERE id NOT IN (SELECT id FROM t2_i0024)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0024
   WHERE id NOT IN (SELECT id FROM t1_i0024)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0024 a JOIN t2_i0024 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0025
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0025, t2_i0025;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0025 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0025 MODIFY target BINARY(20) NOT NULL, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0025 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0025 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0025' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0025
   WHERE id NOT IN (SELECT id FROM t2_i0025)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0025
   WHERE id NOT IN (SELECT id FROM t1_i0025)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0025 a JOIN t2_i0025 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0026
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0026, t2_i0026;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0026 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0026 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0026 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0026 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0026' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0026
   WHERE id NOT IN (SELECT id FROM t2_i0026)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0026
   WHERE id NOT IN (SELECT id FROM t1_i0026)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0026 a JOIN t2_i0026 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0027
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0027, t2_i0027;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0027 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(10) NOT NULL DEFAULT 0x00,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0027 MODIFY target BINARY(20) NOT NULL DEFAULT 0x00, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0027 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(20)
CREATE TABLE t2_i0027 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(20) NOT NULL DEFAULT 0x00,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0027' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0027
   WHERE id NOT IN (SELECT id FROM t2_i0027)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0027
   WHERE id NOT IN (SELECT id FROM t1_i0027)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0027 a JOIN t2_i0027 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0028
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_i0028, t2_i0028;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0028 (
  target BINARY(10),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0028 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0028 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0028 (target) VALUES (0x000000000000000000);
INSERT INTO t1_i0028 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_i0028 (target) VALUES ('');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_i0028 MODIFY target BINARY(20), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0028 (target) VALUES (0x0000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0028 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0028 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0028 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_i0028 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_i0028 (target) VALUES ('');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0028 (target) VALUES (0x414141414141414141414141414141414141414141);
-- Oracle table: BINARY(10)
CREATE TABLE t2_i0028 (
  target BINARY(10),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0028 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0028 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0028 (target) VALUES (0x000000000000000000);
INSERT INTO t2_i0028 (target) VALUES (0x41424142414241424142);
INSERT INTO t2_i0028 (target) VALUES ('');
INSERT INTO t2_i0028 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_i0028 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0028 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0028 (target) VALUES (0x00000000000000000000);
INSERT INTO t2_i0028 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_i0028 (target) VALUES ('');
SELECT 'TC-I0028' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0028
   WHERE id NOT IN (SELECT id FROM t2_i0028)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0028
   WHERE id NOT IN (SELECT id FROM t1_i0028)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0028 a JOIN t2_i0028 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-IA0029
-- Column attribute preservation: COMMENT
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_ia0029, t2_tc_ia0029;
CREATE TABLE t1_tc_ia0029 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target BINARY(10) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_ia0029 (target) VALUES (0x00000000000000000000);
INSERT INTO t1_tc_ia0029 (target) VALUES (0xffffffffffffffffffff);
INSERT INTO t1_tc_ia0029 (target) VALUES (0x000000000000000000);
INSERT INTO t1_tc_ia0029 (target) VALUES (0x41424142414241424142);
INSERT INTO t1_tc_ia0029 (target) VALUES ('');
ALTER TABLE t1_tc_ia0029 MODIFY target BINARY(20) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_ia0029 (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t1_tc_ia0029 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_tc_ia0029 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d4d);
SELECT 'TC-IA0029' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_ia0029' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-I0030
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0030, t2_i0030;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0030 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0030 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0030 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0030 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0030 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0030 (target) VALUES ('');
INSERT INTO t1_i0030 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0030 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0030 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0030 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0030 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0030 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0030 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0030 (target) VALUES ('');
INSERT INTO t1_i0030 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0030 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0030 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0030 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0030 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0030 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0030 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0030 (target) VALUES ('');
INSERT INTO t2_i0030 (target) VALUES (NULL);
INSERT INTO t2_i0030 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0030 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0030 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0030 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0030 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0030 (target) VALUES ('');
INSERT INTO t2_i0030 (target) VALUES (NULL);
SELECT 'TC-I0030' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0030
   WHERE id NOT IN (SELECT id FROM t2_i0030)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0030
   WHERE id NOT IN (SELECT id FROM t1_i0030)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0030 a JOIN t2_i0030 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0031
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0031, t2_i0031;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0031 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t1_i0031 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0031 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0031 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0031 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0031 (target) VALUES ('');
INSERT INTO t1_i0031 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0031 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0031 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0031 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0031 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0031 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0031 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0031 (target) VALUES ('');
INSERT INTO t1_i0031 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0031 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0031 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t2_i0031 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0031 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0031 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0031 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0031 (target) VALUES ('');
INSERT INTO t2_i0031 (target) VALUES (NULL);
INSERT INTO t2_i0031 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0031 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0031 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0031 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0031 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0031 (target) VALUES ('');
INSERT INTO t2_i0031 (target) VALUES (NULL);
SELECT 'TC-I0031' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0031
   WHERE id NOT IN (SELECT id FROM t2_i0031)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0031
   WHERE id NOT IN (SELECT id FROM t1_i0031)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0031 a JOIN t2_i0031 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0032
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0032, t2_i0032;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0032 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t1_i0032 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0032 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0032 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0032 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0032 (target) VALUES ('');
INSERT INTO t1_i0032 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0032 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0032 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0032 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0032 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0032 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0032 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0032 (target) VALUES ('');
INSERT INTO t1_i0032 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0032 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0032 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t2_i0032 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0032 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0032 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0032 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0032 (target) VALUES ('');
INSERT INTO t2_i0032 (target) VALUES (NULL);
INSERT INTO t2_i0032 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0032 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0032 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0032 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0032 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0032 (target) VALUES ('');
INSERT INTO t2_i0032 (target) VALUES (NULL);
SELECT 'TC-I0032' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0032
   WHERE id NOT IN (SELECT id FROM t2_i0032)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0032
   WHERE id NOT IN (SELECT id FROM t1_i0032)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0032 a JOIN t2_i0032 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0033
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0033, t2_i0033;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0033 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0033 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0033 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0033 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0033 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0033 (target) VALUES ('');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_i0033 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0033 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0033 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0033 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0033 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0033 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0033 (target) VALUES ('');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0033 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(40)
CREATE TABLE t2_i0033 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0033 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0033 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0033 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0033 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0033 (target) VALUES ('');
INSERT INTO t2_i0033 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0033 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0033 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0033 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0033 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0033 (target) VALUES ('');
SELECT 'TC-I0033' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0033
   WHERE id NOT IN (SELECT id FROM t2_i0033)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0033
   WHERE id NOT IN (SELECT id FROM t1_i0033)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0033 a JOIN t2_i0033 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0034
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0034, t2_i0034;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0034 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0034 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0034 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0034 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0034 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0034 (target) VALUES ('');
INSERT INTO t1_i0034 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0034 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0034 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0034 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0034 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0034 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0034 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0034 (target) VALUES ('');
INSERT INTO t1_i0034 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0034 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0034 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0034 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0034 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0034 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0034 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0034 (target) VALUES ('');
INSERT INTO t2_i0034 (target) VALUES (NULL);
INSERT INTO t2_i0034 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0034 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0034 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0034 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0034 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0034 (target) VALUES ('');
INSERT INTO t2_i0034 (target) VALUES (NULL);
SELECT 'TC-I0034' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0034
   WHERE id NOT IN (SELECT id FROM t2_i0034)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0034
   WHERE id NOT IN (SELECT id FROM t1_i0034)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0034 a JOIN t2_i0034 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0035
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0035, t2_i0035;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0035 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0035 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0035 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0035 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0035 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0035 (target) VALUES ('');
INSERT INTO t1_i0035 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0035 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0035 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0035 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0035 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0035 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0035 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0035 (target) VALUES ('');
INSERT INTO t1_i0035 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0035 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0035 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0035 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0035 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0035 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0035 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0035 (target) VALUES ('');
INSERT INTO t2_i0035 (target) VALUES (NULL);
INSERT INTO t2_i0035 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0035 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0035 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0035 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0035 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0035 (target) VALUES ('');
INSERT INTO t2_i0035 (target) VALUES (NULL);
SELECT 'TC-I0035' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0035
   WHERE id NOT IN (SELECT id FROM t2_i0035)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0035
   WHERE id NOT IN (SELECT id FROM t1_i0035)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0035 a JOIN t2_i0035 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0036
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0036, t2_i0036;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0036 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0036 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0036 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0036 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0036 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0036 (target) VALUES ('');
INSERT INTO t1_i0036 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0036 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0036 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0036 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0036 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0036 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0036 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0036 (target) VALUES ('');
INSERT INTO t1_i0036 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0036 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0036 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0036 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0036 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0036 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0036 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0036 (target) VALUES ('');
INSERT INTO t2_i0036 (target) VALUES (NULL);
INSERT INTO t2_i0036 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0036 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0036 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0036 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0036 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0036 (target) VALUES ('');
INSERT INTO t2_i0036 (target) VALUES (NULL);
SELECT 'TC-I0036' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0036
   WHERE id NOT IN (SELECT id FROM t2_i0036)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0036
   WHERE id NOT IN (SELECT id FROM t1_i0036)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0036 a JOIN t2_i0036 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0037
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0037, t2_i0037;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0037 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0037 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0037 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0037 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0037 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0037 (target) VALUES ('');
INSERT INTO t1_i0037 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0037 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0037 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0037 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0037 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0037 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0037 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0037 (target) VALUES ('');
INSERT INTO t1_i0037 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0037 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0037 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0037 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0037 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0037 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0037 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0037 (target) VALUES ('');
INSERT INTO t2_i0037 (target) VALUES (NULL);
INSERT INTO t2_i0037 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0037 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0037 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0037 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0037 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0037 (target) VALUES ('');
INSERT INTO t2_i0037 (target) VALUES (NULL);
SELECT 'TC-I0037' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0037
   WHERE id NOT IN (SELECT id FROM t2_i0037)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0037
   WHERE id NOT IN (SELECT id FROM t1_i0037)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0037 a JOIN t2_i0037 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0038
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0038, t2_i0038;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0038 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0038 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0038 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0038 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0038 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0038 (target) VALUES ('');
INSERT INTO t1_i0038 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0038 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0038 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0038 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0038 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0038 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0038 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0038 (target) VALUES ('');
INSERT INTO t1_i0038 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0038 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0038 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0038 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0038 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0038 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0038 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0038 (target) VALUES ('');
INSERT INTO t2_i0038 (target) VALUES (NULL);
INSERT INTO t2_i0038 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0038 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0038 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0038 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0038 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0038 (target) VALUES ('');
INSERT INTO t2_i0038 (target) VALUES (NULL);
SELECT 'TC-I0038' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0038
   WHERE id NOT IN (SELECT id FROM t2_i0038)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0038
   WHERE id NOT IN (SELECT id FROM t1_i0038)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0038 a JOIN t2_i0038 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0039
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_i0039, t2_i0039;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0039 (
  target BINARY(40),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0039 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0039 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0039 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0039 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0039 (target) VALUES ('');
INSERT INTO t1_i0039 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0039 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0039 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0039 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0039 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0039 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0039 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0039 (target) VALUES ('');
INSERT INTO t1_i0039 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0039 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0039 (
  target BINARY(80),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0039 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0039 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0039 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0039 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0039 (target) VALUES ('');
INSERT INTO t2_i0039 (target) VALUES (NULL);
INSERT INTO t2_i0039 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0039 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0039 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0039 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0039 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0039 (target) VALUES ('');
INSERT INTO t2_i0039 (target) VALUES (NULL);
SELECT 'TC-I0039' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0039
   WHERE id NOT IN (SELECT id FROM t2_i0039)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0039
   WHERE id NOT IN (SELECT id FROM t1_i0039)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0039 a JOIN t2_i0039 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0040
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_i0040, t2_i0040;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0040 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target BINARY(40), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0040 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0040 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0040 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0040 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0040 (target) VALUES ('');
INSERT INTO t1_i0040 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0040 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0040 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0040 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0040 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0040 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0040 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0040 (target) VALUES ('');
INSERT INTO t1_i0040 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0040 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0040 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target BINARY(80), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0040 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0040 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0040 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0040 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0040 (target) VALUES ('');
INSERT INTO t2_i0040 (target) VALUES (NULL);
INSERT INTO t2_i0040 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0040 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0040 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0040 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0040 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0040 (target) VALUES ('');
INSERT INTO t2_i0040 (target) VALUES (NULL);
SELECT 'TC-I0040' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0040
   WHERE id NOT IN (SELECT id FROM t2_i0040)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0040
   WHERE id NOT IN (SELECT id FROM t1_i0040)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0040 a JOIN t2_i0040 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0041
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0041, t2_i0041;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0041 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0041 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0041 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0041 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0041 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0041 (target) VALUES ('');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0041 MODIFY target BINARY(80) NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0041 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0041 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0041 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0041 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0041 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0041 (target) VALUES ('');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0041 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0041 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0041 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0041 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0041 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0041 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0041 (target) VALUES ('');
INSERT INTO t2_i0041 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0041 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0041 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0041 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0041 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0041 (target) VALUES ('');
SELECT 'TC-I0041' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0041
   WHERE id NOT IN (SELECT id FROM t2_i0041)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0041
   WHERE id NOT IN (SELECT id FROM t1_i0041)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0041 a JOIN t2_i0041 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0042
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0042, t2_i0042;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0042 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40) DEFAULT 0x00,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0042 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0042 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0042 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0042 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0042 (target) VALUES ('');
INSERT INTO t1_i0042 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0042 MODIFY target BINARY(80) DEFAULT 0x00, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0042 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0042 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0042 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0042 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0042 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0042 (target) VALUES ('');
INSERT INTO t1_i0042 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0042 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0042 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80) DEFAULT 0x00,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0042 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0042 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0042 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0042 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0042 (target) VALUES ('');
INSERT INTO t2_i0042 (target) VALUES (NULL);
INSERT INTO t2_i0042 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0042 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0042 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0042 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0042 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0042 (target) VALUES ('');
INSERT INTO t2_i0042 (target) VALUES (NULL);
SELECT 'TC-I0042' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0042
   WHERE id NOT IN (SELECT id FROM t2_i0042)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0042
   WHERE id NOT IN (SELECT id FROM t1_i0042)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0042 a JOIN t2_i0042 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0043
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0043, t2_i0043;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0043 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0043 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0043 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0043 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0043 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0043 (target) VALUES ('');
INSERT INTO t1_i0043 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0043 MODIFY target BINARY(80) DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0043 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0043 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0043 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0043 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0043 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0043 (target) VALUES ('');
INSERT INTO t1_i0043 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0043 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0043 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0043 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0043 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0043 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0043 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0043 (target) VALUES ('');
INSERT INTO t2_i0043 (target) VALUES (NULL);
INSERT INTO t2_i0043 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0043 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0043 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0043 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0043 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0043 (target) VALUES ('');
INSERT INTO t2_i0043 (target) VALUES (NULL);
SELECT 'TC-I0043' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0043
   WHERE id NOT IN (SELECT id FROM t2_i0043)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0043
   WHERE id NOT IN (SELECT id FROM t1_i0043)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0043 a JOIN t2_i0043 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0044
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0044, t2_i0044;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0044 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40) NOT NULL DEFAULT 0x00,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0044 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0044 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0044 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0044 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0044 (target) VALUES ('');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0044 MODIFY target BINARY(80) NOT NULL DEFAULT 0x00, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0044 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0044 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0044 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0044 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0044 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0044 (target) VALUES ('');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0044 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0044 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80) NOT NULL DEFAULT 0x00,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0044 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0044 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0044 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0044 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0044 (target) VALUES ('');
INSERT INTO t2_i0044 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0044 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0044 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0044 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0044 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0044 (target) VALUES ('');
SELECT 'TC-I0044' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0044
   WHERE id NOT IN (SELECT id FROM t2_i0044)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0044
   WHERE id NOT IN (SELECT id FROM t1_i0044)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0044 a JOIN t2_i0044 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0045
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0045, t2_i0045;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0045 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0045 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0045 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0045 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0045 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0045 (target) VALUES ('');
INSERT INTO t1_i0045 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0045 MODIFY target BINARY(80) INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0045 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0045 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0045 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0045 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0045 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0045 (target) VALUES ('');
INSERT INTO t1_i0045 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0045 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0045 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0045 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0045 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0045 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0045 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0045 (target) VALUES ('');
INSERT INTO t2_i0045 (target) VALUES (NULL);
INSERT INTO t2_i0045 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0045 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0045 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0045 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0045 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0045 (target) VALUES ('');
INSERT INTO t2_i0045 (target) VALUES (NULL);
SELECT 'TC-I0045' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0045
   WHERE id NOT IN (SELECT id FROM t2_i0045)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0045
   WHERE id NOT IN (SELECT id FROM t1_i0045)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0045 a JOIN t2_i0045 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0046
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0046, t2_i0046;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0046 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0046 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0046 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0046 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0046' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0046
   WHERE id NOT IN (SELECT id FROM t2_i0046)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0046
   WHERE id NOT IN (SELECT id FROM t1_i0046)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0046 a JOIN t2_i0046 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0047
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0047, t2_i0047;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0047 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0047 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0047 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0047 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0047 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0047 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0047 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0047 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0047 (target) VALUES ('');
INSERT INTO t1_i0047 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0047 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0047 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0047 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0047 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0047 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0047 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0047 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0047 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0047 (target) VALUES ('');
INSERT INTO t2_i0047 (target) VALUES (NULL);
SELECT 'TC-I0047' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0047
   WHERE id NOT IN (SELECT id FROM t2_i0047)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0047
   WHERE id NOT IN (SELECT id FROM t1_i0047)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0047 a JOIN t2_i0047 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0048
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0048, t2_i0048;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0048 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0048 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0048 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0048 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0048 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0048 (target) VALUES ('');
INSERT INTO t1_i0048 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0048 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0048 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0048 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0048 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0048 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0048 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0048 (target) VALUES ('');
INSERT INTO t1_i0048 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0048 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0048 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0048 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0048 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0048 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0048 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0048 (target) VALUES ('');
INSERT INTO t2_i0048 (target) VALUES (NULL);
INSERT INTO t2_i0048 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0048 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0048 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0048 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0048 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0048 (target) VALUES ('');
INSERT INTO t2_i0048 (target) VALUES (NULL);
SELECT 'TC-I0048' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0048
   WHERE id NOT IN (SELECT id FROM t2_i0048)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0048
   WHERE id NOT IN (SELECT id FROM t1_i0048)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0048 a JOIN t2_i0048 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0049
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0049, t2_i0049;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0049 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0049 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0049 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0049 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0049 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0049 (target) VALUES ('');
INSERT INTO t1_i0049 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0049 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0049 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0049 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0049 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0049 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0049 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0049 (target) VALUES ('');
INSERT INTO t1_i0049 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0049 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0049 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0049 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0049 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0049 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0049 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0049 (target) VALUES ('');
INSERT INTO t2_i0049 (target) VALUES (NULL);
INSERT INTO t2_i0049 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0049 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0049 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0049 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0049 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0049 (target) VALUES ('');
INSERT INTO t2_i0049 (target) VALUES (NULL);
SELECT 'TC-I0049' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0049
   WHERE id NOT IN (SELECT id FROM t2_i0049)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0049
   WHERE id NOT IN (SELECT id FROM t1_i0049)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0049 a JOIN t2_i0049 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0050
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0050, t2_i0050;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0050 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0050 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0050 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0050 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0050 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0050 (target) VALUES ('');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0050 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0050 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0050 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0050 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0050 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0050 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0050 (target) VALUES ('');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0050 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0050 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0050 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0050 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0050 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0050 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0050 (target) VALUES ('');
INSERT INTO t2_i0050 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0050 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0050 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0050 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0050 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0050 (target) VALUES ('');
SELECT 'TC-I0050' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0050
   WHERE id NOT IN (SELECT id FROM t2_i0050)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0050
   WHERE id NOT IN (SELECT id FROM t1_i0050)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0050 a JOIN t2_i0050 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0051
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0051, t2_i0051;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0051 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0051 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0051 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0051 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0051 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0051 (target) VALUES ('');
INSERT INTO t1_i0051 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0051 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0051 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0051 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0051 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0051 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0051 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0051 (target) VALUES ('');
INSERT INTO t1_i0051 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0051 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0051 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0051 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0051 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0051 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0051 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0051 (target) VALUES ('');
INSERT INTO t2_i0051 (target) VALUES (NULL);
INSERT INTO t2_i0051 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0051 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0051 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0051 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0051 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0051 (target) VALUES ('');
INSERT INTO t2_i0051 (target) VALUES (NULL);
SELECT 'TC-I0051' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0051
   WHERE id NOT IN (SELECT id FROM t2_i0051)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0051
   WHERE id NOT IN (SELECT id FROM t1_i0051)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0051 a JOIN t2_i0051 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0052
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0052, t2_i0052;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0052 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0052 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0052 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0052 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0052 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0052 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0052 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0052 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0052 (target) VALUES ('');
INSERT INTO t1_i0052 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0052 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0052 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0052 (target) VALUES (NULL);
INSERT INTO t2_i0052 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0052 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0052 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0052 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0052 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0052 (target) VALUES ('');
INSERT INTO t2_i0052 (target) VALUES (NULL);
SELECT 'TC-I0052' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0052
   WHERE id NOT IN (SELECT id FROM t2_i0052)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0052
   WHERE id NOT IN (SELECT id FROM t1_i0052)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0052 a JOIN t2_i0052 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0053
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0053, t2_i0053;
SET SESSION sql_mode = '';
CREATE TABLE t1_i0053 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0053 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0053 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0053 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0053 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0053 (target) VALUES ('');
INSERT INTO t1_i0053 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0053 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0053 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0053 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0053 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0053 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0053 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0053 (target) VALUES ('');
INSERT INTO t1_i0053 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0053 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0053 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0053 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0053 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0053 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0053 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0053 (target) VALUES ('');
INSERT INTO t2_i0053 (target) VALUES (NULL);
INSERT INTO t2_i0053 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0053 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0053 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0053 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0053 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0053 (target) VALUES ('');
INSERT INTO t2_i0053 (target) VALUES (NULL);
SELECT 'TC-I0053' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0053
   WHERE id NOT IN (SELECT id FROM t2_i0053)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0053
   WHERE id NOT IN (SELECT id FROM t1_i0053)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0053 a JOIN t2_i0053 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0054
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0054, t2_i0054;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0054 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0054 MODIFY target BINARY(80) NOT NULL, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0054 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0054 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0054' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0054
   WHERE id NOT IN (SELECT id FROM t2_i0054)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0054
   WHERE id NOT IN (SELECT id FROM t1_i0054)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0054 a JOIN t2_i0054 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0055
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0055, t2_i0055;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0055 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0055 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0055 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0055 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0055' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0055
   WHERE id NOT IN (SELECT id FROM t2_i0055)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0055
   WHERE id NOT IN (SELECT id FROM t1_i0055)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0055 a JOIN t2_i0055 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0056
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0056, t2_i0056;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0056 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(40) NOT NULL DEFAULT 0x00,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0056 MODIFY target BINARY(80) NOT NULL DEFAULT 0x00, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0056 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(80)
CREATE TABLE t2_i0056 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BINARY(80) NOT NULL DEFAULT 0x00,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0056' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0056
   WHERE id NOT IN (SELECT id FROM t2_i0056)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0056
   WHERE id NOT IN (SELECT id FROM t1_i0056)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0056 a JOIN t2_i0056 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0057
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_i0057, t2_i0057;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0057 (
  target BINARY(40),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0057 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0057 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0057 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0057 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_i0057 (target) VALUES ('');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_i0057 MODIFY target BINARY(80), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0057 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0057 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0057 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t1_i0057 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_i0057 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_i0057 (target) VALUES ('');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0057 (target) VALUES (0x414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141);
-- Oracle table: BINARY(40)
CREATE TABLE t2_i0057 (
  target BINARY(40),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0057 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0057 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0057 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0057 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t2_i0057 (target) VALUES ('');
INSERT INTO t2_i0057 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0057 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0057 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
INSERT INTO t2_i0057 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_i0057 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_i0057 (target) VALUES ('');
SELECT 'TC-I0057' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0057
   WHERE id NOT IN (SELECT id FROM t2_i0057)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0057
   WHERE id NOT IN (SELECT id FROM t1_i0057)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0057 a JOIN t2_i0057 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-IA0058
-- Column attribute preservation: COMMENT
-- Type: BINARY(40) -> BINARY(80), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_ia0058, t2_tc_ia0058;
CREATE TABLE t1_tc_ia0058 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target BINARY(40) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_ia0058 (target) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_tc_ia0058 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_tc_ia0058 (target) VALUES (0x000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_tc_ia0058 (target) VALUES (0x41424142414241424142414241424142414241424142414241424142414241424142414241424142);
INSERT INTO t1_tc_ia0058 (target) VALUES ('');
ALTER TABLE t1_tc_ia0058 MODIFY target BINARY(80) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_ia0058 (target) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t1_tc_ia0058 (target) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t1_tc_ia0058 (target) VALUES (0x4d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d49584d4d);
SELECT 'TC-IA0058' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_ia0058' AND column_name='target' AND column_comment='test_comment';

