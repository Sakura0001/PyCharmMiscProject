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

-- File 27: 外键表测试(增强类型)

-- Test Case: TC-FI0001
-- FK Scenario: child, Algorithm: instant
-- Type: BINARY(10) -> BINARY(20)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0001, tp_tc_fi0001, t2_tc_fi0001;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0001 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0001 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0001_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0001(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0001 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_fi0001 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_fi0001 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_fi0001 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_fi0001 (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_fi0001 (fk_col) VALUES (0x41424142414241424142);
-- ALTER child table only
ALTER TABLE tc_tc_fi0001 MODIFY fk_col BINARY(20), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0001 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0001 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_fi0001 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_fi0001 (fk_col) VALUES (0x41424142414241424142);
SELECT 'TC-FI0001' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0001
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0001)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0001
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0001)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0001 a JOIN t2_tc_fi0001 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0002
-- FK Scenario: parent, Algorithm: instant
-- Type: BINARY(10) -> BINARY(20)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0002, tp_tc_fi0002, t2_tc_fi0002;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0002 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0002 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0002_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0002(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0002 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_fi0002 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_fi0002 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_fi0002 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_fi0002 (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_fi0002 (fk_col) VALUES (0x41424142414241424142);
-- ALTER parent table only
ALTER TABLE tp_tc_fi0002 MODIFY fk_col BINARY(20), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0002 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0002 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_fi0002 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_fi0002 (fk_col) VALUES (0x41424142414241424142);
SELECT 'TC-FI0002' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0002
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0002)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0002
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0002)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0002 a JOIN t2_tc_fi0002 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0003
-- FK Scenario: both, Algorithm: instant
-- Type: BINARY(10) -> BINARY(20)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0003, tp_tc_fi0003, t2_tc_fi0003;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0003 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0003 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0003_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0003(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0003 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_fi0003 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_fi0003 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_fi0003 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_fi0003 (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_fi0003 (fk_col) VALUES (0x41424142414241424142);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_fi0003 MODIFY fk_col BINARY(20), ALGORITHM=instant;
ALTER TABLE tc_tc_fi0003 MODIFY fk_col BINARY(20), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0003 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0003 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_fi0003 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_fi0003 (fk_col) VALUES (0x41424142414241424142);
SELECT 'TC-FI0003' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0003
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0003)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0003
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0003)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0003 a JOIN t2_tc_fi0003 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0004
-- FK Scenario: non_fk, Algorithm: instant
-- Type: BINARY(10) -> BINARY(20)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0004, tp_tc_fi0004, t2_tc_fi0004;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0004 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0004 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0004_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0004(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0004 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_fi0004 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_fi0004 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_fi0004 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_fi0004 (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_fi0004 (fk_col) VALUES (0x41424142414241424142);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_fi0004 MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0004 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0004 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_fi0004 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_fi0004 (fk_col) VALUES (0x41424142414241424142);
SELECT 'TC-FI0004' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0004
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0004)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0004
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0004)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0004 a JOIN t2_tc_fi0004 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0005
-- FK Scenario: child, Algorithm: inplace
-- Type: BINARY(10) -> BINARY(20)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0005, tp_tc_fi0005, t2_tc_fi0005;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0005 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0005 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0005_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0005(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0005 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_fi0005 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_fi0005 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_fi0005 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_fi0005 (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_fi0005 (fk_col) VALUES (0x41424142414241424142);
-- ALTER child table only
ALTER TABLE tc_tc_fi0005 MODIFY fk_col BINARY(20), ALGORITHM=inplace;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0005 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0005 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_fi0005 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_fi0005 (fk_col) VALUES (0x41424142414241424142);
SELECT 'TC-FI0005' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0005
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0005)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0005
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0005)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0005 a JOIN t2_tc_fi0005 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0006
-- FK Scenario: parent, Algorithm: inplace
-- Type: BINARY(10) -> BINARY(20)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0006, tp_tc_fi0006, t2_tc_fi0006;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0006 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0006 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0006_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0006(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0006 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_fi0006 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_fi0006 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_fi0006 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_fi0006 (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_fi0006 (fk_col) VALUES (0x41424142414241424142);
-- ALTER parent table only
ALTER TABLE tp_tc_fi0006 MODIFY fk_col BINARY(20), ALGORITHM=inplace;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0006 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0006 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_fi0006 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_fi0006 (fk_col) VALUES (0x41424142414241424142);
SELECT 'TC-FI0006' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0006
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0006)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0006
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0006)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0006 a JOIN t2_tc_fi0006 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0007
-- FK Scenario: both, Algorithm: inplace
-- Type: BINARY(10) -> BINARY(20)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0007, tp_tc_fi0007, t2_tc_fi0007;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0007 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0007 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0007_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0007(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0007 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_fi0007 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_fi0007 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_fi0007 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_fi0007 (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_fi0007 (fk_col) VALUES (0x41424142414241424142);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_fi0007 MODIFY fk_col BINARY(20), ALGORITHM=inplace;
ALTER TABLE tc_tc_fi0007 MODIFY fk_col BINARY(20), ALGORITHM=inplace;
INSERT INTO tp_tc_fi0007 (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tc_tc_fi0007 (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tp_tc_fi0007 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_fi0007 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0007 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(20), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0007 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_fi0007 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_fi0007 (fk_col) VALUES (0x41424142414241424142);
INSERT INTO t2_tc_fi0007 (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_tc_fi0007 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-FI0007' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0007
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0007)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0007
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0007)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0007 a JOIN t2_tc_fi0007 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0008
-- FK Scenario: non_fk, Algorithm: inplace
-- Type: BINARY(10) -> BINARY(20)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0008, tp_tc_fi0008, t2_tc_fi0008;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0008 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0008 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0008_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0008(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0008 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_fi0008 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_fi0008 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_fi0008 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_fi0008 (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_fi0008 (fk_col) VALUES (0x41424142414241424142);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_fi0008 MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=inplace;
INSERT INTO tp_tc_fi0008 (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tc_tc_fi0008 (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tp_tc_fi0008 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_fi0008 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0008 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0008 (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_fi0008 (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_fi0008 (fk_col) VALUES (0x41424142414241424142);
INSERT INTO t2_tc_fi0008 (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_tc_fi0008 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-FI0008' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0008
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0008)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0008
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0008)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0008 a JOIN t2_tc_fi0008 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0009
-- FK Scenario: child, Algorithm: instant
-- Type: VARBINARY(50) -> VARBINARY(100)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0009, tp_tc_fi0009, t2_tc_fi0009;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0009 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0009 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0009_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0009(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0009 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_fi0009 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_fi0009 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_fi0009 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER child table only
ALTER TABLE tc_tc_fi0009 MODIFY fk_col VARBINARY(100), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0009 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(50), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0009 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_fi0009 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-FI0009' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0009
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0009)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0009
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0009)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0009 a JOIN t2_tc_fi0009 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0010
-- FK Scenario: parent, Algorithm: instant
-- Type: VARBINARY(50) -> VARBINARY(100)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0010, tp_tc_fi0010, t2_tc_fi0010;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0010 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0010 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0010_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0010(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0010 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_fi0010 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_fi0010 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_fi0010 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER parent table only
ALTER TABLE tp_tc_fi0010 MODIFY fk_col VARBINARY(100), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0010 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(50), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0010 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_fi0010 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-FI0010' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0010
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0010)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0010
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0010)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0010 a JOIN t2_tc_fi0010 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0011
-- FK Scenario: both, Algorithm: instant
-- Type: VARBINARY(50) -> VARBINARY(100)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0011, tp_tc_fi0011, t2_tc_fi0011;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0011 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0011 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0011_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0011(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0011 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_fi0011 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_fi0011 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_fi0011 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_fi0011 MODIFY fk_col VARBINARY(100), ALGORITHM=instant;
ALTER TABLE tc_tc_fi0011 MODIFY fk_col VARBINARY(100), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0011 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(50), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0011 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_fi0011 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-FI0011' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0011
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0011)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0011
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0011)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0011 a JOIN t2_tc_fi0011 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0012
-- FK Scenario: non_fk, Algorithm: instant
-- Type: VARBINARY(50) -> VARBINARY(100)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0012, tp_tc_fi0012, t2_tc_fi0012;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0012 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0012 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0012_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0012(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0012 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_fi0012 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_fi0012 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_fi0012 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_fi0012 MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0012 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(50), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0012 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_fi0012 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-FI0012' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0012
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0012)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0012
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0012)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0012 a JOIN t2_tc_fi0012 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0013
-- FK Scenario: child, Algorithm: inplace
-- Type: VARBINARY(50) -> VARBINARY(100)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0013, tp_tc_fi0013, t2_tc_fi0013;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0013 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0013 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0013_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0013(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0013 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_fi0013 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_fi0013 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_fi0013 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER child table only
ALTER TABLE tc_tc_fi0013 MODIFY fk_col VARBINARY(100), ALGORITHM=inplace;
INSERT INTO tp_tc_fi0013 (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_fi0013 (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0013 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(100), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0013 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_fi0013 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_tc_fi0013 (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
SELECT 'TC-FI0013' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0013
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0013)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0013
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0013)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0013 a JOIN t2_tc_fi0013 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0014
-- FK Scenario: parent, Algorithm: inplace
-- Type: VARBINARY(50) -> VARBINARY(100)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0014, tp_tc_fi0014, t2_tc_fi0014;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0014 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0014 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0014_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0014(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0014 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_fi0014 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_fi0014 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_fi0014 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER parent table only
ALTER TABLE tp_tc_fi0014 MODIFY fk_col VARBINARY(100), ALGORITHM=inplace;
INSERT INTO tp_tc_fi0014 (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_fi0014 (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0014 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(100), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0014 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_fi0014 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_tc_fi0014 (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
SELECT 'TC-FI0014' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0014
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0014)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0014
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0014)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0014 a JOIN t2_tc_fi0014 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0015
-- FK Scenario: both, Algorithm: inplace
-- Type: VARBINARY(50) -> VARBINARY(100)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0015, tp_tc_fi0015, t2_tc_fi0015;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0015 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0015 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0015_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0015(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0015 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_fi0015 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_fi0015 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_fi0015 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_fi0015 MODIFY fk_col VARBINARY(100), ALGORITHM=inplace;
ALTER TABLE tc_tc_fi0015 MODIFY fk_col VARBINARY(100), ALGORITHM=inplace;
INSERT INTO tp_tc_fi0015 (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_fi0015 (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0015 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(100), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0015 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_fi0015 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_tc_fi0015 (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
SELECT 'TC-FI0015' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0015
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0015)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0015
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0015)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0015 a JOIN t2_tc_fi0015 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0016
-- FK Scenario: non_fk, Algorithm: inplace
-- Type: VARBINARY(50) -> VARBINARY(100)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0016, tp_tc_fi0016, t2_tc_fi0016;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0016 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0016 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0016_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0016(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0016 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_fi0016 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_fi0016 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_fi0016 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_fi0016 MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=inplace;
INSERT INTO tp_tc_fi0016 (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_fi0016 (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0016 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(50), data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0016 (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_fi0016 (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_tc_fi0016 (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
SELECT 'TC-FI0016' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0016
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0016)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0016
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0016)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0016 a JOIN t2_tc_fi0016 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0017
-- FK Scenario: child, Algorithm: instant
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0017, tp_tc_fi0017, t2_tc_fi0017;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0017 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0017 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0017_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0017(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0017 (fk_col) VALUES (0.00);
INSERT INTO tc_tc_fi0017 (fk_col) VALUES (0.00);
INSERT INTO tp_tc_fi0017 (fk_col) VALUES (1.23);
INSERT INTO tc_tc_fi0017 (fk_col) VALUES (1.23);
INSERT INTO tp_tc_fi0017 (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_fi0017 (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_fi0017 (fk_col) VALUES (99.99);
INSERT INTO tc_tc_fi0017 (fk_col) VALUES (99.99);
-- ALTER child table only
ALTER TABLE tc_tc_fi0017 MODIFY fk_col DECIMAL(12,2), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0017 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0017 (fk_col) VALUES (0.00);
INSERT INTO t2_tc_fi0017 (fk_col) VALUES (1.23);
INSERT INTO t2_tc_fi0017 (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_fi0017 (fk_col) VALUES (99.99);
SELECT 'TC-FI0017' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0017
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0017)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0017
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0017)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0017 a JOIN t2_tc_fi0017 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0018
-- FK Scenario: parent, Algorithm: instant
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0018, tp_tc_fi0018, t2_tc_fi0018;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0018 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0018 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0018_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0018(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0018 (fk_col) VALUES (0.00);
INSERT INTO tc_tc_fi0018 (fk_col) VALUES (0.00);
INSERT INTO tp_tc_fi0018 (fk_col) VALUES (1.23);
INSERT INTO tc_tc_fi0018 (fk_col) VALUES (1.23);
INSERT INTO tp_tc_fi0018 (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_fi0018 (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_fi0018 (fk_col) VALUES (99.99);
INSERT INTO tc_tc_fi0018 (fk_col) VALUES (99.99);
-- ALTER parent table only
ALTER TABLE tp_tc_fi0018 MODIFY fk_col DECIMAL(12,2), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0018 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0018 (fk_col) VALUES (0.00);
INSERT INTO t2_tc_fi0018 (fk_col) VALUES (1.23);
INSERT INTO t2_tc_fi0018 (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_fi0018 (fk_col) VALUES (99.99);
SELECT 'TC-FI0018' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0018
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0018)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0018
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0018)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0018 a JOIN t2_tc_fi0018 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0019
-- FK Scenario: both, Algorithm: instant
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0019, tp_tc_fi0019, t2_tc_fi0019;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0019 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0019 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0019_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0019(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0019 (fk_col) VALUES (0.00);
INSERT INTO tc_tc_fi0019 (fk_col) VALUES (0.00);
INSERT INTO tp_tc_fi0019 (fk_col) VALUES (1.23);
INSERT INTO tc_tc_fi0019 (fk_col) VALUES (1.23);
INSERT INTO tp_tc_fi0019 (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_fi0019 (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_fi0019 (fk_col) VALUES (99.99);
INSERT INTO tc_tc_fi0019 (fk_col) VALUES (99.99);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_fi0019 MODIFY fk_col DECIMAL(12,2), ALGORITHM=instant;
ALTER TABLE tc_tc_fi0019 MODIFY fk_col DECIMAL(12,2), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0019 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0019 (fk_col) VALUES (0.00);
INSERT INTO t2_tc_fi0019 (fk_col) VALUES (1.23);
INSERT INTO t2_tc_fi0019 (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_fi0019 (fk_col) VALUES (99.99);
SELECT 'TC-FI0019' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0019
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0019)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0019
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0019)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0019 a JOIN t2_tc_fi0019 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0020
-- FK Scenario: non_fk, Algorithm: instant
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0020, tp_tc_fi0020, t2_tc_fi0020;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0020 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0020 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0020_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0020(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0020 (fk_col) VALUES (0.00);
INSERT INTO tc_tc_fi0020 (fk_col) VALUES (0.00);
INSERT INTO tp_tc_fi0020 (fk_col) VALUES (1.23);
INSERT INTO tc_tc_fi0020 (fk_col) VALUES (1.23);
INSERT INTO tp_tc_fi0020 (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_fi0020 (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_fi0020 (fk_col) VALUES (99.99);
INSERT INTO tc_tc_fi0020 (fk_col) VALUES (99.99);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_fi0020 MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0020 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0020 (fk_col) VALUES (0.00);
INSERT INTO t2_tc_fi0020 (fk_col) VALUES (1.23);
INSERT INTO t2_tc_fi0020 (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_fi0020 (fk_col) VALUES (99.99);
SELECT 'TC-FI0020' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0020
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0020)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0020
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0020)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0020 a JOIN t2_tc_fi0020 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0021
-- FK Scenario: child, Algorithm: inplace
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0021, tp_tc_fi0021, t2_tc_fi0021;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0021 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0021 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0021_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0021(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0021 (fk_col) VALUES (0.00);
INSERT INTO tc_tc_fi0021 (fk_col) VALUES (0.00);
INSERT INTO tp_tc_fi0021 (fk_col) VALUES (1.23);
INSERT INTO tc_tc_fi0021 (fk_col) VALUES (1.23);
INSERT INTO tp_tc_fi0021 (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_fi0021 (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_fi0021 (fk_col) VALUES (99.99);
INSERT INTO tc_tc_fi0021 (fk_col) VALUES (99.99);
-- ALTER child table only
ALTER TABLE tc_tc_fi0021 MODIFY fk_col DECIMAL(12,2), ALGORITHM=inplace;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0021 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0021 (fk_col) VALUES (0.00);
INSERT INTO t2_tc_fi0021 (fk_col) VALUES (1.23);
INSERT INTO t2_tc_fi0021 (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_fi0021 (fk_col) VALUES (99.99);
SELECT 'TC-FI0021' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0021
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0021)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0021
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0021)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0021 a JOIN t2_tc_fi0021 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0022
-- FK Scenario: parent, Algorithm: inplace
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0022, tp_tc_fi0022, t2_tc_fi0022;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0022 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0022 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0022_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0022(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0022 (fk_col) VALUES (0.00);
INSERT INTO tc_tc_fi0022 (fk_col) VALUES (0.00);
INSERT INTO tp_tc_fi0022 (fk_col) VALUES (1.23);
INSERT INTO tc_tc_fi0022 (fk_col) VALUES (1.23);
INSERT INTO tp_tc_fi0022 (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_fi0022 (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_fi0022 (fk_col) VALUES (99.99);
INSERT INTO tc_tc_fi0022 (fk_col) VALUES (99.99);
-- ALTER parent table only
ALTER TABLE tp_tc_fi0022 MODIFY fk_col DECIMAL(12,2), ALGORITHM=inplace;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0022 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0022 (fk_col) VALUES (0.00);
INSERT INTO t2_tc_fi0022 (fk_col) VALUES (1.23);
INSERT INTO t2_tc_fi0022 (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_fi0022 (fk_col) VALUES (99.99);
SELECT 'TC-FI0022' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0022
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0022)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0022
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0022)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0022 a JOIN t2_tc_fi0022 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0023
-- FK Scenario: both, Algorithm: inplace
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0023, tp_tc_fi0023, t2_tc_fi0023;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0023 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0023 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0023_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0023(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0023 (fk_col) VALUES (0.00);
INSERT INTO tc_tc_fi0023 (fk_col) VALUES (0.00);
INSERT INTO tp_tc_fi0023 (fk_col) VALUES (1.23);
INSERT INTO tc_tc_fi0023 (fk_col) VALUES (1.23);
INSERT INTO tp_tc_fi0023 (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_fi0023 (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_fi0023 (fk_col) VALUES (99.99);
INSERT INTO tc_tc_fi0023 (fk_col) VALUES (99.99);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_fi0023 MODIFY fk_col DECIMAL(12,2), ALGORITHM=inplace;
ALTER TABLE tc_tc_fi0023 MODIFY fk_col DECIMAL(12,2), ALGORITHM=inplace;
INSERT INTO tp_tc_fi0023 (fk_col) VALUES (999.99);
INSERT INTO tc_tc_fi0023 (fk_col) VALUES (999.99);
INSERT INTO tp_tc_fi0023 (fk_col) VALUES (1000.00);
INSERT INTO tc_tc_fi0023 (fk_col) VALUES (1000.00);
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0023 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(12,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0023 (fk_col) VALUES (0.00);
INSERT INTO t2_tc_fi0023 (fk_col) VALUES (1.23);
INSERT INTO t2_tc_fi0023 (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_fi0023 (fk_col) VALUES (99.99);
INSERT INTO t2_tc_fi0023 (fk_col) VALUES (999.99);
INSERT INTO t2_tc_fi0023 (fk_col) VALUES (1000.00);
SELECT 'TC-FI0023' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0023
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0023)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0023
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0023)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0023 a JOIN t2_tc_fi0023 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FI0024
-- FK Scenario: non_fk, Algorithm: inplace
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fi0024, tp_tc_fi0024, t2_tc_fi0024;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fi0024 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fi0024 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fi0024_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fi0024(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fi0024 (fk_col) VALUES (0.00);
INSERT INTO tc_tc_fi0024 (fk_col) VALUES (0.00);
INSERT INTO tp_tc_fi0024 (fk_col) VALUES (1.23);
INSERT INTO tc_tc_fi0024 (fk_col) VALUES (1.23);
INSERT INTO tp_tc_fi0024 (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_fi0024 (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_fi0024 (fk_col) VALUES (99.99);
INSERT INTO tc_tc_fi0024 (fk_col) VALUES (99.99);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_fi0024 MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=inplace;
INSERT INTO tp_tc_fi0024 (fk_col) VALUES (999.99);
INSERT INTO tc_tc_fi0024 (fk_col) VALUES (999.99);
INSERT INTO tp_tc_fi0024 (fk_col) VALUES (1000.00);
INSERT INTO tc_tc_fi0024 (fk_col) VALUES (1000.00);
-- Oracle table for child comparison
CREATE TABLE t2_tc_fi0024 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fi0024 (fk_col) VALUES (0.00);
INSERT INTO t2_tc_fi0024 (fk_col) VALUES (1.23);
INSERT INTO t2_tc_fi0024 (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_fi0024 (fk_col) VALUES (99.99);
INSERT INTO t2_tc_fi0024 (fk_col) VALUES (999.99);
INSERT INTO t2_tc_fi0024 (fk_col) VALUES (1000.00);
SELECT 'TC-FI0024' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fi0024
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fi0024)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fi0024
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fi0024)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fi0024 a JOIN t2_tc_fi0024 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

