-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 阿里云环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: 整数(SIGNED/UNSIGNED) + CHAR + VARCHAR
-- 覆盖算法: INSTANT + INPLACE
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- 生成时间: 2026-09-20
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

-- File 11: 外键表测试

-- Test Case: TC-FA0001
-- FK Scenario: child, Algorithm: instant
-- Type: INT -> BIGINT
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fa0001, tp_tc_fa0001, t2_tc_fa0001;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fa0001 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fa0001 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fa0001_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fa0001(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fa0001 (fk_col) VALUES (0);
INSERT INTO tc_tc_fa0001 (fk_col) VALUES (0);
INSERT INTO tp_tc_fa0001 (fk_col) VALUES (1);
INSERT INTO tc_tc_fa0001 (fk_col) VALUES (1);
INSERT INTO tp_tc_fa0001 (fk_col) VALUES (-1);
INSERT INTO tc_tc_fa0001 (fk_col) VALUES (-1);
INSERT INTO tp_tc_fa0001 (fk_col) VALUES (42);
INSERT INTO tc_tc_fa0001 (fk_col) VALUES (42);
INSERT INTO tp_tc_fa0001 (fk_col) VALUES (127);
INSERT INTO tc_tc_fa0001 (fk_col) VALUES (127);
-- ALTER child table only
ALTER TABLE tc_tc_fa0001 MODIFY fk_col BIGINT, ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fa0001 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fa0001 (fk_col) VALUES (0);
INSERT INTO t2_tc_fa0001 (fk_col) VALUES (1);
INSERT INTO t2_tc_fa0001 (fk_col) VALUES (-1);
INSERT INTO t2_tc_fa0001 (fk_col) VALUES (42);
INSERT INTO t2_tc_fa0001 (fk_col) VALUES (127);
SELECT 'TC-FA0001' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fa0001
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fa0001)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fa0001
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fa0001)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fa0001 a JOIN t2_tc_fa0001 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FA0002
-- FK Scenario: parent, Algorithm: instant
-- Type: INT -> BIGINT
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fa0002, tp_tc_fa0002, t2_tc_fa0002;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fa0002 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fa0002 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fa0002_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fa0002(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fa0002 (fk_col) VALUES (0);
INSERT INTO tc_tc_fa0002 (fk_col) VALUES (0);
INSERT INTO tp_tc_fa0002 (fk_col) VALUES (1);
INSERT INTO tc_tc_fa0002 (fk_col) VALUES (1);
INSERT INTO tp_tc_fa0002 (fk_col) VALUES (-1);
INSERT INTO tc_tc_fa0002 (fk_col) VALUES (-1);
INSERT INTO tp_tc_fa0002 (fk_col) VALUES (42);
INSERT INTO tc_tc_fa0002 (fk_col) VALUES (42);
INSERT INTO tp_tc_fa0002 (fk_col) VALUES (127);
INSERT INTO tc_tc_fa0002 (fk_col) VALUES (127);
-- ALTER parent table only
ALTER TABLE tp_tc_fa0002 MODIFY fk_col BIGINT, ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fa0002 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fa0002 (fk_col) VALUES (0);
INSERT INTO t2_tc_fa0002 (fk_col) VALUES (1);
INSERT INTO t2_tc_fa0002 (fk_col) VALUES (-1);
INSERT INTO t2_tc_fa0002 (fk_col) VALUES (42);
INSERT INTO t2_tc_fa0002 (fk_col) VALUES (127);
SELECT 'TC-FA0002' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fa0002
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fa0002)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fa0002
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fa0002)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fa0002 a JOIN t2_tc_fa0002 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FA0003
-- FK Scenario: both, Algorithm: instant
-- Type: INT -> BIGINT
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fa0003, tp_tc_fa0003, t2_tc_fa0003;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fa0003 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fa0003 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fa0003_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fa0003(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fa0003 (fk_col) VALUES (0);
INSERT INTO tc_tc_fa0003 (fk_col) VALUES (0);
INSERT INTO tp_tc_fa0003 (fk_col) VALUES (1);
INSERT INTO tc_tc_fa0003 (fk_col) VALUES (1);
INSERT INTO tp_tc_fa0003 (fk_col) VALUES (-1);
INSERT INTO tc_tc_fa0003 (fk_col) VALUES (-1);
INSERT INTO tp_tc_fa0003 (fk_col) VALUES (42);
INSERT INTO tc_tc_fa0003 (fk_col) VALUES (42);
INSERT INTO tp_tc_fa0003 (fk_col) VALUES (127);
INSERT INTO tc_tc_fa0003 (fk_col) VALUES (127);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_fa0003 MODIFY fk_col BIGINT, ALGORITHM=instant;
ALTER TABLE tc_tc_fa0003 MODIFY fk_col BIGINT, ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fa0003 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fa0003 (fk_col) VALUES (0);
INSERT INTO t2_tc_fa0003 (fk_col) VALUES (1);
INSERT INTO t2_tc_fa0003 (fk_col) VALUES (-1);
INSERT INTO t2_tc_fa0003 (fk_col) VALUES (42);
INSERT INTO t2_tc_fa0003 (fk_col) VALUES (127);
SELECT 'TC-FA0003' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fa0003
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fa0003)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fa0003
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fa0003)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fa0003 a JOIN t2_tc_fa0003 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FA0004
-- FK Scenario: non_fk, Algorithm: instant
-- Type: INT -> BIGINT
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fa0004, tp_tc_fa0004, t2_tc_fa0004;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fa0004 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fa0004 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fa0004_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fa0004(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fa0004 (fk_col) VALUES (0);
INSERT INTO tc_tc_fa0004 (fk_col) VALUES (0);
INSERT INTO tp_tc_fa0004 (fk_col) VALUES (1);
INSERT INTO tc_tc_fa0004 (fk_col) VALUES (1);
INSERT INTO tp_tc_fa0004 (fk_col) VALUES (-1);
INSERT INTO tc_tc_fa0004 (fk_col) VALUES (-1);
INSERT INTO tp_tc_fa0004 (fk_col) VALUES (42);
INSERT INTO tc_tc_fa0004 (fk_col) VALUES (42);
INSERT INTO tp_tc_fa0004 (fk_col) VALUES (127);
INSERT INTO tc_tc_fa0004 (fk_col) VALUES (127);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_fa0004 MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=instant;
INSERT INTO tp_tc_fa0004 (fk_col) VALUES (128);
INSERT INTO tc_tc_fa0004 (fk_col) VALUES (128);
INSERT INTO tp_tc_fa0004 (fk_col) VALUES (255);
INSERT INTO tc_tc_fa0004 (fk_col) VALUES (255);
INSERT INTO tp_tc_fa0004 (fk_col) VALUES (1000);
INSERT INTO tc_tc_fa0004 (fk_col) VALUES (1000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_fa0004 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fa0004 (fk_col) VALUES (0);
INSERT INTO t2_tc_fa0004 (fk_col) VALUES (1);
INSERT INTO t2_tc_fa0004 (fk_col) VALUES (-1);
INSERT INTO t2_tc_fa0004 (fk_col) VALUES (42);
INSERT INTO t2_tc_fa0004 (fk_col) VALUES (127);
INSERT INTO t2_tc_fa0004 (fk_col) VALUES (128);
INSERT INTO t2_tc_fa0004 (fk_col) VALUES (255);
INSERT INTO t2_tc_fa0004 (fk_col) VALUES (1000);
SELECT 'TC-FA0004' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fa0004
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fa0004)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fa0004
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fa0004)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fa0004 a JOIN t2_tc_fa0004 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FA0005
-- FK Scenario: child, Algorithm: inplace
-- Type: INT -> BIGINT
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fa0005, tp_tc_fa0005, t2_tc_fa0005;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fa0005 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fa0005 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fa0005_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fa0005(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fa0005 (fk_col) VALUES (0);
INSERT INTO tc_tc_fa0005 (fk_col) VALUES (0);
INSERT INTO tp_tc_fa0005 (fk_col) VALUES (1);
INSERT INTO tc_tc_fa0005 (fk_col) VALUES (1);
INSERT INTO tp_tc_fa0005 (fk_col) VALUES (-1);
INSERT INTO tc_tc_fa0005 (fk_col) VALUES (-1);
INSERT INTO tp_tc_fa0005 (fk_col) VALUES (42);
INSERT INTO tc_tc_fa0005 (fk_col) VALUES (42);
INSERT INTO tp_tc_fa0005 (fk_col) VALUES (127);
INSERT INTO tc_tc_fa0005 (fk_col) VALUES (127);
-- ALTER child table only
ALTER TABLE tc_tc_fa0005 MODIFY fk_col BIGINT, ALGORITHM=inplace;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fa0005 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fa0005 (fk_col) VALUES (0);
INSERT INTO t2_tc_fa0005 (fk_col) VALUES (1);
INSERT INTO t2_tc_fa0005 (fk_col) VALUES (-1);
INSERT INTO t2_tc_fa0005 (fk_col) VALUES (42);
INSERT INTO t2_tc_fa0005 (fk_col) VALUES (127);
SELECT 'TC-FA0005' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fa0005
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fa0005)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fa0005
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fa0005)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fa0005 a JOIN t2_tc_fa0005 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FA0006
-- FK Scenario: parent, Algorithm: inplace
-- Type: INT -> BIGINT
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fa0006, tp_tc_fa0006, t2_tc_fa0006;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fa0006 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fa0006 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fa0006_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fa0006(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fa0006 (fk_col) VALUES (0);
INSERT INTO tc_tc_fa0006 (fk_col) VALUES (0);
INSERT INTO tp_tc_fa0006 (fk_col) VALUES (1);
INSERT INTO tc_tc_fa0006 (fk_col) VALUES (1);
INSERT INTO tp_tc_fa0006 (fk_col) VALUES (-1);
INSERT INTO tc_tc_fa0006 (fk_col) VALUES (-1);
INSERT INTO tp_tc_fa0006 (fk_col) VALUES (42);
INSERT INTO tc_tc_fa0006 (fk_col) VALUES (42);
INSERT INTO tp_tc_fa0006 (fk_col) VALUES (127);
INSERT INTO tc_tc_fa0006 (fk_col) VALUES (127);
-- ALTER parent table only
ALTER TABLE tp_tc_fa0006 MODIFY fk_col BIGINT, ALGORITHM=inplace;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fa0006 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fa0006 (fk_col) VALUES (0);
INSERT INTO t2_tc_fa0006 (fk_col) VALUES (1);
INSERT INTO t2_tc_fa0006 (fk_col) VALUES (-1);
INSERT INTO t2_tc_fa0006 (fk_col) VALUES (42);
INSERT INTO t2_tc_fa0006 (fk_col) VALUES (127);
SELECT 'TC-FA0006' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fa0006
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fa0006)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fa0006
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fa0006)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fa0006 a JOIN t2_tc_fa0006 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FA0007
-- FK Scenario: both, Algorithm: inplace
-- Type: INT -> BIGINT
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fa0007, tp_tc_fa0007, t2_tc_fa0007;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fa0007 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fa0007 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fa0007_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fa0007(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fa0007 (fk_col) VALUES (0);
INSERT INTO tc_tc_fa0007 (fk_col) VALUES (0);
INSERT INTO tp_tc_fa0007 (fk_col) VALUES (1);
INSERT INTO tc_tc_fa0007 (fk_col) VALUES (1);
INSERT INTO tp_tc_fa0007 (fk_col) VALUES (-1);
INSERT INTO tc_tc_fa0007 (fk_col) VALUES (-1);
INSERT INTO tp_tc_fa0007 (fk_col) VALUES (42);
INSERT INTO tc_tc_fa0007 (fk_col) VALUES (42);
INSERT INTO tp_tc_fa0007 (fk_col) VALUES (127);
INSERT INTO tc_tc_fa0007 (fk_col) VALUES (127);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_fa0007 MODIFY fk_col BIGINT, ALGORITHM=inplace;
ALTER TABLE tc_tc_fa0007 MODIFY fk_col BIGINT, ALGORITHM=inplace;
INSERT INTO tp_tc_fa0007 (fk_col) VALUES (128);
INSERT INTO tc_tc_fa0007 (fk_col) VALUES (128);
INSERT INTO tp_tc_fa0007 (fk_col) VALUES (255);
INSERT INTO tc_tc_fa0007 (fk_col) VALUES (255);
INSERT INTO tp_tc_fa0007 (fk_col) VALUES (1000);
INSERT INTO tc_tc_fa0007 (fk_col) VALUES (1000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_fa0007 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BIGINT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fa0007 (fk_col) VALUES (0);
INSERT INTO t2_tc_fa0007 (fk_col) VALUES (1);
INSERT INTO t2_tc_fa0007 (fk_col) VALUES (-1);
INSERT INTO t2_tc_fa0007 (fk_col) VALUES (42);
INSERT INTO t2_tc_fa0007 (fk_col) VALUES (127);
INSERT INTO t2_tc_fa0007 (fk_col) VALUES (128);
INSERT INTO t2_tc_fa0007 (fk_col) VALUES (255);
INSERT INTO t2_tc_fa0007 (fk_col) VALUES (1000);
SELECT 'TC-FA0007' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fa0007
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fa0007)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fa0007
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fa0007)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fa0007 a JOIN t2_tc_fa0007 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FA0008
-- FK Scenario: non_fk, Algorithm: inplace
-- Type: INT -> BIGINT
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fa0008, tp_tc_fa0008, t2_tc_fa0008;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fa0008 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fa0008 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fa0008_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fa0008(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fa0008 (fk_col) VALUES (0);
INSERT INTO tc_tc_fa0008 (fk_col) VALUES (0);
INSERT INTO tp_tc_fa0008 (fk_col) VALUES (1);
INSERT INTO tc_tc_fa0008 (fk_col) VALUES (1);
INSERT INTO tp_tc_fa0008 (fk_col) VALUES (-1);
INSERT INTO tc_tc_fa0008 (fk_col) VALUES (-1);
INSERT INTO tp_tc_fa0008 (fk_col) VALUES (42);
INSERT INTO tc_tc_fa0008 (fk_col) VALUES (42);
INSERT INTO tp_tc_fa0008 (fk_col) VALUES (127);
INSERT INTO tc_tc_fa0008 (fk_col) VALUES (127);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_fa0008 MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=inplace;
INSERT INTO tp_tc_fa0008 (fk_col) VALUES (128);
INSERT INTO tc_tc_fa0008 (fk_col) VALUES (128);
INSERT INTO tp_tc_fa0008 (fk_col) VALUES (255);
INSERT INTO tc_tc_fa0008 (fk_col) VALUES (255);
INSERT INTO tp_tc_fa0008 (fk_col) VALUES (1000);
INSERT INTO tc_tc_fa0008 (fk_col) VALUES (1000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_fa0008 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fa0008 (fk_col) VALUES (0);
INSERT INTO t2_tc_fa0008 (fk_col) VALUES (1);
INSERT INTO t2_tc_fa0008 (fk_col) VALUES (-1);
INSERT INTO t2_tc_fa0008 (fk_col) VALUES (42);
INSERT INTO t2_tc_fa0008 (fk_col) VALUES (127);
INSERT INTO t2_tc_fa0008 (fk_col) VALUES (128);
INSERT INTO t2_tc_fa0008 (fk_col) VALUES (255);
INSERT INTO t2_tc_fa0008 (fk_col) VALUES (1000);
SELECT 'TC-FA0008' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fa0008
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fa0008)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fa0008
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fa0008)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fa0008 a JOIN t2_tc_fa0008 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FA0009
-- FK Scenario: child, Algorithm: instant
-- Type: VARCHAR(50) -> VARCHAR(100)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fa0009, tp_tc_fa0009, t2_tc_fa0009;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fa0009 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fa0009 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fa0009_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fa0009(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fa0009 (fk_col) VALUES ('hello');
INSERT INTO tc_tc_fa0009 (fk_col) VALUES ('hello');
INSERT INTO tp_tc_fa0009 (fk_col) VALUES ('world');
INSERT INTO tc_tc_fa0009 (fk_col) VALUES ('world');
INSERT INTO tp_tc_fa0009 (fk_col) VALUES ('test');
INSERT INTO tc_tc_fa0009 (fk_col) VALUES ('test');
INSERT INTO tp_tc_fa0009 (fk_col) VALUES ('abc');
INSERT INTO tc_tc_fa0009 (fk_col) VALUES ('abc');
-- ALTER child table only
ALTER TABLE tc_tc_fa0009 MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fa0009 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(50) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fa0009 (fk_col) VALUES ('hello');
INSERT INTO t2_tc_fa0009 (fk_col) VALUES ('world');
INSERT INTO t2_tc_fa0009 (fk_col) VALUES ('test');
INSERT INTO t2_tc_fa0009 (fk_col) VALUES ('abc');
SELECT 'TC-FA0009' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fa0009
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fa0009)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fa0009
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fa0009)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fa0009 a JOIN t2_tc_fa0009 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FA0010
-- FK Scenario: parent, Algorithm: instant
-- Type: VARCHAR(50) -> VARCHAR(100)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fa0010, tp_tc_fa0010, t2_tc_fa0010;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fa0010 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fa0010 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fa0010_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fa0010(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fa0010 (fk_col) VALUES ('hello');
INSERT INTO tc_tc_fa0010 (fk_col) VALUES ('hello');
INSERT INTO tp_tc_fa0010 (fk_col) VALUES ('world');
INSERT INTO tc_tc_fa0010 (fk_col) VALUES ('world');
INSERT INTO tp_tc_fa0010 (fk_col) VALUES ('test');
INSERT INTO tc_tc_fa0010 (fk_col) VALUES ('test');
INSERT INTO tp_tc_fa0010 (fk_col) VALUES ('abc');
INSERT INTO tc_tc_fa0010 (fk_col) VALUES ('abc');
-- ALTER parent table only
ALTER TABLE tp_tc_fa0010 MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fa0010 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(50) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fa0010 (fk_col) VALUES ('hello');
INSERT INTO t2_tc_fa0010 (fk_col) VALUES ('world');
INSERT INTO t2_tc_fa0010 (fk_col) VALUES ('test');
INSERT INTO t2_tc_fa0010 (fk_col) VALUES ('abc');
SELECT 'TC-FA0010' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fa0010
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fa0010)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fa0010
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fa0010)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fa0010 a JOIN t2_tc_fa0010 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FA0011
-- FK Scenario: both, Algorithm: instant
-- Type: VARCHAR(50) -> VARCHAR(100)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fa0011, tp_tc_fa0011, t2_tc_fa0011;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fa0011 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fa0011 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fa0011_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fa0011(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fa0011 (fk_col) VALUES ('hello');
INSERT INTO tc_tc_fa0011 (fk_col) VALUES ('hello');
INSERT INTO tp_tc_fa0011 (fk_col) VALUES ('world');
INSERT INTO tc_tc_fa0011 (fk_col) VALUES ('world');
INSERT INTO tp_tc_fa0011 (fk_col) VALUES ('test');
INSERT INTO tc_tc_fa0011 (fk_col) VALUES ('test');
INSERT INTO tp_tc_fa0011 (fk_col) VALUES ('abc');
INSERT INTO tc_tc_fa0011 (fk_col) VALUES ('abc');
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_fa0011 MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=instant;
ALTER TABLE tc_tc_fa0011 MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_fa0011 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(50) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fa0011 (fk_col) VALUES ('hello');
INSERT INTO t2_tc_fa0011 (fk_col) VALUES ('world');
INSERT INTO t2_tc_fa0011 (fk_col) VALUES ('test');
INSERT INTO t2_tc_fa0011 (fk_col) VALUES ('abc');
SELECT 'TC-FA0011' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fa0011
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fa0011)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fa0011
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fa0011)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fa0011 a JOIN t2_tc_fa0011 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FA0012
-- FK Scenario: non_fk, Algorithm: instant
-- Type: VARCHAR(50) -> VARCHAR(100)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fa0012, tp_tc_fa0012, t2_tc_fa0012;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fa0012 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fa0012 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fa0012_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fa0012(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fa0012 (fk_col) VALUES ('hello');
INSERT INTO tc_tc_fa0012 (fk_col) VALUES ('hello');
INSERT INTO tp_tc_fa0012 (fk_col) VALUES ('world');
INSERT INTO tc_tc_fa0012 (fk_col) VALUES ('world');
INSERT INTO tp_tc_fa0012 (fk_col) VALUES ('test');
INSERT INTO tc_tc_fa0012 (fk_col) VALUES ('test');
INSERT INTO tp_tc_fa0012 (fk_col) VALUES ('abc');
INSERT INTO tc_tc_fa0012 (fk_col) VALUES ('abc');
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_fa0012 MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=instant;
INSERT INTO tp_tc_fa0012 (fk_col) VALUES ('hello_world');
INSERT INTO tc_tc_fa0012 (fk_col) VALUES ('hello_world');
INSERT INTO tp_tc_fa0012 (fk_col) VALUES ('a');
INSERT INTO tc_tc_fa0012 (fk_col) VALUES ('a');
-- Oracle table for child comparison
CREATE TABLE t2_tc_fa0012 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(50) CHARACTER SET latin1, data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fa0012 (fk_col) VALUES ('hello');
INSERT INTO t2_tc_fa0012 (fk_col) VALUES ('world');
INSERT INTO t2_tc_fa0012 (fk_col) VALUES ('test');
INSERT INTO t2_tc_fa0012 (fk_col) VALUES ('abc');
INSERT INTO t2_tc_fa0012 (fk_col) VALUES ('hello_world');
INSERT INTO t2_tc_fa0012 (fk_col) VALUES ('a');
SELECT 'TC-FA0012' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fa0012
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fa0012)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fa0012
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fa0012)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fa0012 a JOIN t2_tc_fa0012 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FA0013
-- FK Scenario: child, Algorithm: inplace
-- Type: VARCHAR(50) -> VARCHAR(100)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fa0013, tp_tc_fa0013, t2_tc_fa0013;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fa0013 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fa0013 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fa0013_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fa0013(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fa0013 (fk_col) VALUES ('hello');
INSERT INTO tc_tc_fa0013 (fk_col) VALUES ('hello');
INSERT INTO tp_tc_fa0013 (fk_col) VALUES ('world');
INSERT INTO tc_tc_fa0013 (fk_col) VALUES ('world');
INSERT INTO tp_tc_fa0013 (fk_col) VALUES ('test');
INSERT INTO tc_tc_fa0013 (fk_col) VALUES ('test');
INSERT INTO tp_tc_fa0013 (fk_col) VALUES ('abc');
INSERT INTO tc_tc_fa0013 (fk_col) VALUES ('abc');
-- ALTER child table only
ALTER TABLE tc_tc_fa0013 MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=inplace;
INSERT INTO tp_tc_fa0013 (fk_col) VALUES ('hello_world');
INSERT INTO tc_tc_fa0013 (fk_col) VALUES ('hello_world');
INSERT INTO tp_tc_fa0013 (fk_col) VALUES ('a');
INSERT INTO tc_tc_fa0013 (fk_col) VALUES ('a');
-- Oracle table for child comparison
CREATE TABLE t2_tc_fa0013 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(100) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fa0013 (fk_col) VALUES ('hello');
INSERT INTO t2_tc_fa0013 (fk_col) VALUES ('world');
INSERT INTO t2_tc_fa0013 (fk_col) VALUES ('test');
INSERT INTO t2_tc_fa0013 (fk_col) VALUES ('abc');
INSERT INTO t2_tc_fa0013 (fk_col) VALUES ('hello_world');
INSERT INTO t2_tc_fa0013 (fk_col) VALUES ('a');
SELECT 'TC-FA0013' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fa0013
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fa0013)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fa0013
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fa0013)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fa0013 a JOIN t2_tc_fa0013 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FA0014
-- FK Scenario: parent, Algorithm: inplace
-- Type: VARCHAR(50) -> VARCHAR(100)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fa0014, tp_tc_fa0014, t2_tc_fa0014;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fa0014 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fa0014 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fa0014_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fa0014(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fa0014 (fk_col) VALUES ('hello');
INSERT INTO tc_tc_fa0014 (fk_col) VALUES ('hello');
INSERT INTO tp_tc_fa0014 (fk_col) VALUES ('world');
INSERT INTO tc_tc_fa0014 (fk_col) VALUES ('world');
INSERT INTO tp_tc_fa0014 (fk_col) VALUES ('test');
INSERT INTO tc_tc_fa0014 (fk_col) VALUES ('test');
INSERT INTO tp_tc_fa0014 (fk_col) VALUES ('abc');
INSERT INTO tc_tc_fa0014 (fk_col) VALUES ('abc');
-- ALTER parent table only
ALTER TABLE tp_tc_fa0014 MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=inplace;
INSERT INTO tp_tc_fa0014 (fk_col) VALUES ('hello_world');
INSERT INTO tc_tc_fa0014 (fk_col) VALUES ('hello_world');
INSERT INTO tp_tc_fa0014 (fk_col) VALUES ('a');
INSERT INTO tc_tc_fa0014 (fk_col) VALUES ('a');
-- Oracle table for child comparison
CREATE TABLE t2_tc_fa0014 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(100) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fa0014 (fk_col) VALUES ('hello');
INSERT INTO t2_tc_fa0014 (fk_col) VALUES ('world');
INSERT INTO t2_tc_fa0014 (fk_col) VALUES ('test');
INSERT INTO t2_tc_fa0014 (fk_col) VALUES ('abc');
INSERT INTO t2_tc_fa0014 (fk_col) VALUES ('hello_world');
INSERT INTO t2_tc_fa0014 (fk_col) VALUES ('a');
SELECT 'TC-FA0014' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fa0014
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fa0014)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fa0014
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fa0014)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fa0014 a JOIN t2_tc_fa0014 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FA0015
-- FK Scenario: both, Algorithm: inplace
-- Type: VARCHAR(50) -> VARCHAR(100)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fa0015, tp_tc_fa0015, t2_tc_fa0015;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fa0015 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fa0015 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fa0015_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fa0015(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fa0015 (fk_col) VALUES ('hello');
INSERT INTO tc_tc_fa0015 (fk_col) VALUES ('hello');
INSERT INTO tp_tc_fa0015 (fk_col) VALUES ('world');
INSERT INTO tc_tc_fa0015 (fk_col) VALUES ('world');
INSERT INTO tp_tc_fa0015 (fk_col) VALUES ('test');
INSERT INTO tc_tc_fa0015 (fk_col) VALUES ('test');
INSERT INTO tp_tc_fa0015 (fk_col) VALUES ('abc');
INSERT INTO tc_tc_fa0015 (fk_col) VALUES ('abc');
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_fa0015 MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=inplace;
ALTER TABLE tc_tc_fa0015 MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=inplace;
INSERT INTO tp_tc_fa0015 (fk_col) VALUES ('hello_world');
INSERT INTO tc_tc_fa0015 (fk_col) VALUES ('hello_world');
INSERT INTO tp_tc_fa0015 (fk_col) VALUES ('a');
INSERT INTO tc_tc_fa0015 (fk_col) VALUES ('a');
-- Oracle table for child comparison
CREATE TABLE t2_tc_fa0015 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(100) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fa0015 (fk_col) VALUES ('hello');
INSERT INTO t2_tc_fa0015 (fk_col) VALUES ('world');
INSERT INTO t2_tc_fa0015 (fk_col) VALUES ('test');
INSERT INTO t2_tc_fa0015 (fk_col) VALUES ('abc');
INSERT INTO t2_tc_fa0015 (fk_col) VALUES ('hello_world');
INSERT INTO t2_tc_fa0015 (fk_col) VALUES ('a');
SELECT 'TC-FA0015' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fa0015
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fa0015)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fa0015
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fa0015)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fa0015 a JOIN t2_tc_fa0015 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-FA0016
-- FK Scenario: non_fk, Algorithm: inplace
-- Type: VARCHAR(50) -> VARCHAR(100)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_fa0016, tp_tc_fa0016, t2_tc_fa0016;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_fa0016 (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_fa0016 (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_fa0016_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_fa0016(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_fa0016 (fk_col) VALUES ('hello');
INSERT INTO tc_tc_fa0016 (fk_col) VALUES ('hello');
INSERT INTO tp_tc_fa0016 (fk_col) VALUES ('world');
INSERT INTO tc_tc_fa0016 (fk_col) VALUES ('world');
INSERT INTO tp_tc_fa0016 (fk_col) VALUES ('test');
INSERT INTO tc_tc_fa0016 (fk_col) VALUES ('test');
INSERT INTO tp_tc_fa0016 (fk_col) VALUES ('abc');
INSERT INTO tc_tc_fa0016 (fk_col) VALUES ('abc');
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_fa0016 MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=inplace;
INSERT INTO tp_tc_fa0016 (fk_col) VALUES ('hello_world');
INSERT INTO tc_tc_fa0016 (fk_col) VALUES ('hello_world');
INSERT INTO tp_tc_fa0016 (fk_col) VALUES ('a');
INSERT INTO tc_tc_fa0016 (fk_col) VALUES ('a');
-- Oracle table for child comparison
CREATE TABLE t2_tc_fa0016 (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(50) CHARACTER SET latin1, data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_fa0016 (fk_col) VALUES ('hello');
INSERT INTO t2_tc_fa0016 (fk_col) VALUES ('world');
INSERT INTO t2_tc_fa0016 (fk_col) VALUES ('test');
INSERT INTO t2_tc_fa0016 (fk_col) VALUES ('abc');
INSERT INTO t2_tc_fa0016 (fk_col) VALUES ('hello_world');
INSERT INTO t2_tc_fa0016 (fk_col) VALUES ('a');
SELECT 'TC-FA0016' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_fa0016
   WHERE cid NOT IN (SELECT cid FROM t2_tc_fa0016)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_fa0016
   WHERE cid NOT IN (SELECT cid FROM tc_tc_fa0016)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_fa0016 a JOIN t2_tc_fa0016 b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

