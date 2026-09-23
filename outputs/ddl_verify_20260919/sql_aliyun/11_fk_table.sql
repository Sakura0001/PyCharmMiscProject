-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 阿里云环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: 整数(SIGNED/UNSIGNED) + CHAR + VARCHAR
-- 覆盖算法: INSTANT + INPLACE
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- Suite-Revision: 3c46cd9910b1   (生成器源码哈希; 时间戳见 results/generation_manifest.json)
-- 用例 ID 规则: TC-<文件号>-<作用域>-<序号>-<IT|IP>  —— 全局唯一
--   作用域 REG=普通表 OFAT/二元组, ATR=列属性保持, SPE=特殊模式,
--          FK=外键, PTK=分区(目标列是分区键), PNK=分区(目标列非分区键)
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

-- File 11: 外键表测试

-- Test Case: TC-11-FK-0001-IT
-- FK Scenario: child, Algorithm: instant
-- Type: INT -> BIGINT
-- FK Transition: FK-INT
-- Expected: FAIL
-- @expect alter=FAIL errno=[3780] build=SUCCESS assertions=5 alter_sha=be7a1e4e8ddc
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0001_it, tp_tc_11_fk_0001_it, t2_tc_11_fk_0001_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0001_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0001_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0001_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0001_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0001_it (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0001_it (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0001_it (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0001_it (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0001_it (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0001_it (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0001_it (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0001_it (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0001_it (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0001_it (fk_col) VALUES (127);
-- ALTER child table only
ALTER TABLE tc_tc_11_fk_0001_it MODIFY fk_col BIGINT, ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0001_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0001_it (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0001_it (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0001_it (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0001_it (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0001_it (fk_col) VALUES (127);
SELECT 'TC-11-FK-0001-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0001_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0001_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0001_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0001_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0001_it a JOIN t2_tc_11_fk_0001_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0001-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0001_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0001-IT#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0001_it' AND column_name='data';
SELECT 'TC-11-FK-0001-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0001_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0001-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0001_it_fk on tc_tc_11_fk_0001_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0001_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0001_it_fk';

-- Test Case: TC-11-FK-0002-IT
-- FK Scenario: parent, Algorithm: instant
-- Type: INT -> BIGINT
-- FK Transition: FK-INT
-- Expected: FAIL
-- @expect alter=FAIL errno=[3780] build=SUCCESS assertions=5 alter_sha=0b1feb049fed
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0002_it, tp_tc_11_fk_0002_it, t2_tc_11_fk_0002_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0002_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0002_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0002_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0002_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0002_it (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0002_it (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0002_it (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0002_it (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0002_it (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0002_it (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0002_it (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0002_it (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0002_it (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0002_it (fk_col) VALUES (127);
-- ALTER parent table only
ALTER TABLE tp_tc_11_fk_0002_it MODIFY fk_col BIGINT, ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0002_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0002_it (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0002_it (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0002_it (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0002_it (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0002_it (fk_col) VALUES (127);
SELECT 'TC-11-FK-0002-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0002_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0002_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0002_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0002_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0002_it a JOIN t2_tc_11_fk_0002_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0002-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0002_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0002-IT#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0002_it' AND column_name='data';
SELECT 'TC-11-FK-0002-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0002_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0002-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0002_it_fk on tc_tc_11_fk_0002_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0002_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0002_it_fk';

-- Test Case: TC-11-FK-0003-IT
-- FK Scenario: both, Algorithm: instant
-- Type: INT -> BIGINT
-- FK Transition: FK-INT
-- Expected: FAIL
-- @expect alter=FAIL errno=[3780] build=SUCCESS assertions=5 alter_sha=c87e6c045e95 alter_sha=26380565b529
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0003_it, tp_tc_11_fk_0003_it, t2_tc_11_fk_0003_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0003_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0003_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0003_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0003_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0003_it (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0003_it (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0003_it (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0003_it (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0003_it (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0003_it (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0003_it (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0003_it (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0003_it (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0003_it (fk_col) VALUES (127);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_11_fk_0003_it MODIFY fk_col BIGINT, ALGORITHM=instant;

ALTER TABLE tc_tc_11_fk_0003_it MODIFY fk_col BIGINT, ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0003_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0003_it (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0003_it (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0003_it (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0003_it (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0003_it (fk_col) VALUES (127);
SELECT 'TC-11-FK-0003-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0003_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0003_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0003_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0003_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0003_it a JOIN t2_tc_11_fk_0003_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0003-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0003_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0003-IT#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0003_it' AND column_name='data';
SELECT 'TC-11-FK-0003-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0003_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0003-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0003_it_fk on tc_tc_11_fk_0003_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0003_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0003_it_fk';

-- Test Case: TC-11-FK-0004-IT
-- FK Scenario: both_fkc0, Algorithm: instant
-- Type: INT -> BIGINT
-- FK Transition: FK-INT
-- Expected: FAIL
-- @expect alter=FAIL errno=[3780] build=SUCCESS assertions=5 alter_sha=bc65310748fb alter_sha=51b3b711784b
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0004_it, tp_tc_11_fk_0004_it, t2_tc_11_fk_0004_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0004_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0004_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0004_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0004_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0004_it (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0004_it (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0004_it (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0004_it (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0004_it (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0004_it (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0004_it (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0004_it (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0004_it (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0004_it (fk_col) VALUES (127);
-- 实测: foreign_key_checks=0 并不能绕过 errno 3780
SET foreign_key_checks=0;
-- ALTER parent with fk_checks=0
ALTER TABLE tp_tc_11_fk_0004_it MODIFY fk_col BIGINT, ALGORITHM=instant;

ALTER TABLE tc_tc_11_fk_0004_it MODIFY fk_col BIGINT, ALGORITHM=instant;
SET foreign_key_checks=1;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0004_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0004_it (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0004_it (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0004_it (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0004_it (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0004_it (fk_col) VALUES (127);
SELECT 'TC-11-FK-0004-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0004_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0004_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0004_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0004_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0004_it a JOIN t2_tc_11_fk_0004_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0004-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0004_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0004-IT#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0004_it' AND column_name='data';
SELECT 'TC-11-FK-0004-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0004_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0004-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0004_it_fk on tc_tc_11_fk_0004_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0004_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0004_it_fk';

-- Test Case: TC-11-FK-0005-IT
-- FK Scenario: both_drop_fk, Algorithm: instant
-- Type: INT -> BIGINT
-- FK Transition: FK-INT
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845] build=SUCCESS assertions=5 alter_sha=894b6a3debef alter_sha=0356e762af08
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0005_it, tp_tc_11_fk_0005_it, t2_tc_11_fk_0005_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0005_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0005_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0005_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0005_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0005_it (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0005_it (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0005_it (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0005_it (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0005_it (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0005_it (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0005_it (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0005_it (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0005_it (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0005_it (fk_col) VALUES (127);
-- 正确序列: DROP FOREIGN KEY -> 改两侧 -> ADD FOREIGN KEY
ALTER TABLE tc_tc_11_fk_0005_it DROP FOREIGN KEY tc_11_fk_0005_it_fk;
-- ALTER parent (FK 已摘除)
ALTER TABLE tp_tc_11_fk_0005_it MODIFY fk_col BIGINT, ALGORITHM=instant;

ALTER TABLE tc_tc_11_fk_0005_it MODIFY fk_col BIGINT, ALGORITHM=instant;
ALTER TABLE tc_tc_11_fk_0005_it ADD CONSTRAINT tc_11_fk_0005_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0005_it(fk_col);
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0005_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0005_it (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0005_it (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0005_it (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0005_it (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0005_it (fk_col) VALUES (127);
SELECT 'TC-11-FK-0005-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0005_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0005_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0005_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0005_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0005_it a JOIN t2_tc_11_fk_0005_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0005-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0005_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0005-IT#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0005_it' AND column_name='data';
SELECT 'TC-11-FK-0005-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0005_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0005-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0005_it_fk on tc_tc_11_fk_0005_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0005_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0005_it_fk';

-- Test Case: TC-11-FK-0006-IT
-- FK Scenario: non_fk, Algorithm: instant
-- Type: INT -> BIGINT
-- FK Transition: FK-INT
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=4 alter_sha=882fb0be39b9
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0006_it, tp_tc_11_fk_0006_it, t2_tc_11_fk_0006_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0006_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0006_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0006_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0006_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0006_it (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0006_it (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0006_it (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0006_it (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0006_it (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0006_it (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0006_it (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0006_it (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0006_it (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0006_it (fk_col) VALUES (127);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_11_fk_0006_it MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=instant;
INSERT INTO tp_tc_11_fk_0006_it (fk_col) VALUES (128);
INSERT INTO tc_tc_11_fk_0006_it (fk_col) VALUES (128);
INSERT INTO tp_tc_11_fk_0006_it (fk_col) VALUES (255);
INSERT INTO tc_tc_11_fk_0006_it (fk_col) VALUES (255);
INSERT INTO tp_tc_11_fk_0006_it (fk_col) VALUES (1000);
INSERT INTO tc_tc_11_fk_0006_it (fk_col) VALUES (1000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0006_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0006_it (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0006_it (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0006_it (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0006_it (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0006_it (fk_col) VALUES (127);
INSERT INTO t2_tc_11_fk_0006_it (fk_col) VALUES (128);
INSERT INTO t2_tc_11_fk_0006_it (fk_col) VALUES (255);
INSERT INTO t2_tc_11_fk_0006_it (fk_col) VALUES (1000);
SELECT 'TC-11-FK-0006-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0006_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0006_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0006_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0006_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0006_it a JOIN t2_tc_11_fk_0006_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0006-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0006_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0006-IT#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0006_it' AND column_name='data';
SELECT 'TC-11-FK-0006-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0006_it' AND column_name='fk_col';

-- Test Case: TC-11-FK-0007-IP
-- FK Scenario: child, Algorithm: inplace
-- Type: INT -> BIGINT
-- FK Transition: FK-INT
-- Expected: FAIL
-- @expect alter=FAIL errno=[3780] build=SUCCESS assertions=5 alter_sha=79483e9bc7d8
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0007_ip, tp_tc_11_fk_0007_ip, t2_tc_11_fk_0007_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0007_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0007_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0007_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0007_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0007_ip (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0007_ip (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0007_ip (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0007_ip (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0007_ip (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0007_ip (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0007_ip (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0007_ip (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0007_ip (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0007_ip (fk_col) VALUES (127);
-- ALTER child table only
ALTER TABLE tc_tc_11_fk_0007_ip MODIFY fk_col BIGINT, ALGORITHM=inplace;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0007_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0007_ip (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0007_ip (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0007_ip (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0007_ip (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0007_ip (fk_col) VALUES (127);
SELECT 'TC-11-FK-0007-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0007_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0007_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0007_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0007_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0007_ip a JOIN t2_tc_11_fk_0007_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0007-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0007_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0007-IP#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0007_ip' AND column_name='data';
SELECT 'TC-11-FK-0007-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0007_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0007-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0007_ip_fk on tc_tc_11_fk_0007_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0007_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0007_ip_fk';

-- Test Case: TC-11-FK-0008-IP
-- FK Scenario: parent, Algorithm: inplace
-- Type: INT -> BIGINT
-- FK Transition: FK-INT
-- Expected: FAIL
-- @expect alter=FAIL errno=[3780] build=SUCCESS assertions=5 alter_sha=7532163764dd
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0008_ip, tp_tc_11_fk_0008_ip, t2_tc_11_fk_0008_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0008_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0008_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0008_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0008_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0008_ip (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0008_ip (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0008_ip (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0008_ip (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0008_ip (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0008_ip (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0008_ip (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0008_ip (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0008_ip (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0008_ip (fk_col) VALUES (127);
-- ALTER parent table only
ALTER TABLE tp_tc_11_fk_0008_ip MODIFY fk_col BIGINT, ALGORITHM=inplace;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0008_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0008_ip (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0008_ip (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0008_ip (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0008_ip (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0008_ip (fk_col) VALUES (127);
SELECT 'TC-11-FK-0008-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0008_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0008_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0008_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0008_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0008_ip a JOIN t2_tc_11_fk_0008_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0008-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0008_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0008-IP#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0008_ip' AND column_name='data';
SELECT 'TC-11-FK-0008-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0008_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0008-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0008_ip_fk on tc_tc_11_fk_0008_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0008_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0008_ip_fk';

-- Test Case: TC-11-FK-0009-IP
-- FK Scenario: both, Algorithm: inplace
-- Type: INT -> BIGINT
-- FK Transition: FK-INT
-- Expected: FAIL
-- @expect alter=FAIL errno=[3780] build=SUCCESS assertions=5 alter_sha=3e013e65a5b9 alter_sha=1edab96c5773
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0009_ip, tp_tc_11_fk_0009_ip, t2_tc_11_fk_0009_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0009_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0009_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0009_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0009_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0009_ip (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0009_ip (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0009_ip (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0009_ip (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0009_ip (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0009_ip (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0009_ip (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0009_ip (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0009_ip (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0009_ip (fk_col) VALUES (127);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_11_fk_0009_ip MODIFY fk_col BIGINT, ALGORITHM=inplace;

ALTER TABLE tc_tc_11_fk_0009_ip MODIFY fk_col BIGINT, ALGORITHM=inplace;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0009_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0009_ip (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0009_ip (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0009_ip (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0009_ip (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0009_ip (fk_col) VALUES (127);
SELECT 'TC-11-FK-0009-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0009_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0009_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0009_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0009_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0009_ip a JOIN t2_tc_11_fk_0009_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0009-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0009_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0009-IP#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0009_ip' AND column_name='data';
SELECT 'TC-11-FK-0009-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0009_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0009-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0009_ip_fk on tc_tc_11_fk_0009_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0009_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0009_ip_fk';

-- Test Case: TC-11-FK-0010-IP
-- FK Scenario: both_fkc0, Algorithm: inplace
-- Type: INT -> BIGINT
-- FK Transition: FK-INT
-- Expected: FAIL
-- @expect alter=FAIL errno=[3780] build=SUCCESS assertions=5 alter_sha=0b5bbeef3b55 alter_sha=ea66ae30ae4b
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0010_ip, tp_tc_11_fk_0010_ip, t2_tc_11_fk_0010_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0010_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0010_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0010_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0010_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0010_ip (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0010_ip (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0010_ip (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0010_ip (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0010_ip (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0010_ip (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0010_ip (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0010_ip (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0010_ip (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0010_ip (fk_col) VALUES (127);
-- 实测: foreign_key_checks=0 并不能绕过 errno 3780
SET foreign_key_checks=0;
-- ALTER parent with fk_checks=0
ALTER TABLE tp_tc_11_fk_0010_ip MODIFY fk_col BIGINT, ALGORITHM=inplace;

ALTER TABLE tc_tc_11_fk_0010_ip MODIFY fk_col BIGINT, ALGORITHM=inplace;
SET foreign_key_checks=1;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0010_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0010_ip (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0010_ip (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0010_ip (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0010_ip (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0010_ip (fk_col) VALUES (127);
SELECT 'TC-11-FK-0010-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0010_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0010_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0010_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0010_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0010_ip a JOIN t2_tc_11_fk_0010_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0010-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0010_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0010-IP#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0010_ip' AND column_name='data';
SELECT 'TC-11-FK-0010-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0010_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0010-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0010_ip_fk on tc_tc_11_fk_0010_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0010_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0010_ip_fk';

-- Test Case: TC-11-FK-0011-IP
-- FK Scenario: both_drop_fk, Algorithm: inplace
-- Type: INT -> BIGINT
-- FK Transition: FK-INT
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=5 alter_sha=44fb33045def alter_sha=b122e55c596c
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0011_ip, tp_tc_11_fk_0011_ip, t2_tc_11_fk_0011_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0011_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0011_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0011_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0011_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0011_ip (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0011_ip (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0011_ip (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0011_ip (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0011_ip (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0011_ip (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0011_ip (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0011_ip (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0011_ip (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0011_ip (fk_col) VALUES (127);
-- 正确序列: DROP FOREIGN KEY -> 改两侧 -> ADD FOREIGN KEY
ALTER TABLE tc_tc_11_fk_0011_ip DROP FOREIGN KEY tc_11_fk_0011_ip_fk;
-- ALTER parent (FK 已摘除)
ALTER TABLE tp_tc_11_fk_0011_ip MODIFY fk_col BIGINT, ALGORITHM=inplace;

ALTER TABLE tc_tc_11_fk_0011_ip MODIFY fk_col BIGINT, ALGORITHM=inplace;
ALTER TABLE tc_tc_11_fk_0011_ip ADD CONSTRAINT tc_11_fk_0011_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0011_ip(fk_col);
INSERT INTO tp_tc_11_fk_0011_ip (fk_col) VALUES (128);
INSERT INTO tc_tc_11_fk_0011_ip (fk_col) VALUES (128);
INSERT INTO tp_tc_11_fk_0011_ip (fk_col) VALUES (255);
INSERT INTO tc_tc_11_fk_0011_ip (fk_col) VALUES (255);
INSERT INTO tp_tc_11_fk_0011_ip (fk_col) VALUES (1000);
INSERT INTO tc_tc_11_fk_0011_ip (fk_col) VALUES (1000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0011_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BIGINT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0011_ip (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0011_ip (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0011_ip (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0011_ip (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0011_ip (fk_col) VALUES (127);
INSERT INTO t2_tc_11_fk_0011_ip (fk_col) VALUES (128);
INSERT INTO t2_tc_11_fk_0011_ip (fk_col) VALUES (255);
INSERT INTO t2_tc_11_fk_0011_ip (fk_col) VALUES (1000);
SELECT 'TC-11-FK-0011-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0011_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0011_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0011_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0011_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0011_ip a JOIN t2_tc_11_fk_0011_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0011-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='bigint'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=bigint nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0011_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0011-IP#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0011_ip' AND column_name='data';
SELECT 'TC-11-FK-0011-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='bigint'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=bigint nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0011_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0011-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0011_ip_fk on tc_tc_11_fk_0011_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0011_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0011_ip_fk';

-- Test Case: TC-11-FK-0012-IP
-- FK Scenario: non_fk, Algorithm: inplace
-- Type: INT -> BIGINT
-- FK Transition: FK-INT
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=4 alter_sha=1cd95f5e35d2
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0012_ip, tp_tc_11_fk_0012_ip, t2_tc_11_fk_0012_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0012_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0012_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0012_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0012_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0012_ip (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0012_ip (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0012_ip (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0012_ip (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0012_ip (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0012_ip (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0012_ip (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0012_ip (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0012_ip (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0012_ip (fk_col) VALUES (127);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_11_fk_0012_ip MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=inplace;
INSERT INTO tp_tc_11_fk_0012_ip (fk_col) VALUES (128);
INSERT INTO tc_tc_11_fk_0012_ip (fk_col) VALUES (128);
INSERT INTO tp_tc_11_fk_0012_ip (fk_col) VALUES (255);
INSERT INTO tc_tc_11_fk_0012_ip (fk_col) VALUES (255);
INSERT INTO tp_tc_11_fk_0012_ip (fk_col) VALUES (1000);
INSERT INTO tc_tc_11_fk_0012_ip (fk_col) VALUES (1000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0012_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0012_ip (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0012_ip (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0012_ip (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0012_ip (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0012_ip (fk_col) VALUES (127);
INSERT INTO t2_tc_11_fk_0012_ip (fk_col) VALUES (128);
INSERT INTO t2_tc_11_fk_0012_ip (fk_col) VALUES (255);
INSERT INTO t2_tc_11_fk_0012_ip (fk_col) VALUES (1000);
SELECT 'TC-11-FK-0012-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0012_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0012_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0012_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0012_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0012_ip a JOIN t2_tc_11_fk_0012_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0012-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0012_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0012-IP#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0012_ip' AND column_name='data';
SELECT 'TC-11-FK-0012-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=int nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0012_ip' AND column_name='fk_col';

-- Test Case: TC-11-FK-0013-IT
-- FK Scenario: child, Algorithm: instant
-- Type: VARCHAR(50) -> VARCHAR(100)
-- FK Transition: FK-VC
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845] build=SUCCESS assertions=5 alter_sha=15a406a0c9af
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0013_it, tp_tc_11_fk_0013_it, t2_tc_11_fk_0013_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0013_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0013_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0013_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0013_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0013_it (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0013_it (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0013_it (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0013_it (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0013_it (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0013_it (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0013_it (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0013_it (fk_col) VALUES ('abc');
-- ALTER child table only
ALTER TABLE tc_tc_11_fk_0013_it MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0013_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(50) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0013_it (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0013_it (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0013_it (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0013_it (fk_col) VALUES ('abc');
SELECT 'TC-11-FK-0013-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0013_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0013_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0013_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0013_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0013_it a JOIN t2_tc_11_fk_0013_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0013-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0013_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0013-IT#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0013_it' AND column_name='data';
SELECT 'TC-11-FK-0013-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0013_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0013-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0013_it_fk on tc_tc_11_fk_0013_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0013_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0013_it_fk';

-- Test Case: TC-11-FK-0014-IT
-- FK Scenario: parent, Algorithm: instant
-- Type: VARCHAR(50) -> VARCHAR(100)
-- FK Transition: FK-VC
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845] build=SUCCESS assertions=5 alter_sha=886b28878394
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0014_it, tp_tc_11_fk_0014_it, t2_tc_11_fk_0014_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0014_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0014_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0014_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0014_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0014_it (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0014_it (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0014_it (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0014_it (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0014_it (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0014_it (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0014_it (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0014_it (fk_col) VALUES ('abc');
-- ALTER parent table only
ALTER TABLE tp_tc_11_fk_0014_it MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0014_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(50) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0014_it (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0014_it (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0014_it (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0014_it (fk_col) VALUES ('abc');
SELECT 'TC-11-FK-0014-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0014_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0014_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0014_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0014_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0014_it a JOIN t2_tc_11_fk_0014_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0014-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0014_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0014-IT#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0014_it' AND column_name='data';
SELECT 'TC-11-FK-0014-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0014_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0014-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0014_it_fk on tc_tc_11_fk_0014_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0014_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0014_it_fk';

-- Test Case: TC-11-FK-0015-IT
-- FK Scenario: both, Algorithm: instant
-- Type: VARCHAR(50) -> VARCHAR(100)
-- FK Transition: FK-VC
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845] build=SUCCESS assertions=5 alter_sha=6fa0c1bbcaf8 alter_sha=8018d0892612
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0015_it, tp_tc_11_fk_0015_it, t2_tc_11_fk_0015_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0015_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0015_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0015_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0015_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0015_it (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0015_it (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0015_it (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0015_it (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0015_it (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0015_it (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0015_it (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0015_it (fk_col) VALUES ('abc');
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_11_fk_0015_it MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=instant;

ALTER TABLE tc_tc_11_fk_0015_it MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0015_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(50) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0015_it (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0015_it (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0015_it (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0015_it (fk_col) VALUES ('abc');
SELECT 'TC-11-FK-0015-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0015_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0015_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0015_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0015_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0015_it a JOIN t2_tc_11_fk_0015_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0015-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0015_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0015-IT#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0015_it' AND column_name='data';
SELECT 'TC-11-FK-0015-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0015_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0015-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0015_it_fk on tc_tc_11_fk_0015_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0015_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0015_it_fk';

-- Test Case: TC-11-FK-0016-IT
-- FK Scenario: both_fkc0, Algorithm: instant
-- Type: VARCHAR(50) -> VARCHAR(100)
-- FK Transition: FK-VC
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845] build=SUCCESS assertions=5 alter_sha=e88243c60b23 alter_sha=7a0cc715eddb
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0016_it, tp_tc_11_fk_0016_it, t2_tc_11_fk_0016_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0016_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0016_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0016_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0016_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0016_it (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0016_it (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0016_it (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0016_it (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0016_it (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0016_it (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0016_it (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0016_it (fk_col) VALUES ('abc');
-- 实测: foreign_key_checks=0 并不能绕过 errno 3780
SET foreign_key_checks=0;
-- ALTER parent with fk_checks=0
ALTER TABLE tp_tc_11_fk_0016_it MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=instant;

ALTER TABLE tc_tc_11_fk_0016_it MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=instant;
SET foreign_key_checks=1;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0016_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(50) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0016_it (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0016_it (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0016_it (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0016_it (fk_col) VALUES ('abc');
SELECT 'TC-11-FK-0016-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0016_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0016_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0016_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0016_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0016_it a JOIN t2_tc_11_fk_0016_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0016-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0016_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0016-IT#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0016_it' AND column_name='data';
SELECT 'TC-11-FK-0016-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0016_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0016-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0016_it_fk on tc_tc_11_fk_0016_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0016_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0016_it_fk';

-- Test Case: TC-11-FK-0017-IT
-- FK Scenario: both_drop_fk, Algorithm: instant
-- Type: VARCHAR(50) -> VARCHAR(100)
-- FK Transition: FK-VC
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845] build=SUCCESS assertions=5 alter_sha=15815bc7ef01 alter_sha=57115d708431
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0017_it, tp_tc_11_fk_0017_it, t2_tc_11_fk_0017_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0017_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0017_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0017_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0017_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0017_it (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0017_it (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0017_it (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0017_it (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0017_it (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0017_it (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0017_it (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0017_it (fk_col) VALUES ('abc');
-- 正确序列: DROP FOREIGN KEY -> 改两侧 -> ADD FOREIGN KEY
ALTER TABLE tc_tc_11_fk_0017_it DROP FOREIGN KEY tc_11_fk_0017_it_fk;
-- ALTER parent (FK 已摘除)
ALTER TABLE tp_tc_11_fk_0017_it MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=instant;

ALTER TABLE tc_tc_11_fk_0017_it MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=instant;
ALTER TABLE tc_tc_11_fk_0017_it ADD CONSTRAINT tc_11_fk_0017_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0017_it(fk_col);
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0017_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(50) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0017_it (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0017_it (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0017_it (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0017_it (fk_col) VALUES ('abc');
SELECT 'TC-11-FK-0017-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0017_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0017_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0017_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0017_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0017_it a JOIN t2_tc_11_fk_0017_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0017-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0017_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0017-IT#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0017_it' AND column_name='data';
SELECT 'TC-11-FK-0017-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0017_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0017-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0017_it_fk on tc_tc_11_fk_0017_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0017_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0017_it_fk';

-- Test Case: TC-11-FK-0018-IT
-- FK Scenario: non_fk, Algorithm: instant
-- Type: VARCHAR(50) -> VARCHAR(100)
-- FK Transition: FK-VC
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=4 alter_sha=f675a8c22c6a
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0018_it, tp_tc_11_fk_0018_it, t2_tc_11_fk_0018_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0018_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0018_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0018_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0018_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0018_it (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0018_it (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0018_it (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0018_it (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0018_it (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0018_it (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0018_it (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0018_it (fk_col) VALUES ('abc');
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_11_fk_0018_it MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=instant;
INSERT INTO tp_tc_11_fk_0018_it (fk_col) VALUES ('hello_world');
INSERT INTO tc_tc_11_fk_0018_it (fk_col) VALUES ('hello_world');
INSERT INTO tp_tc_11_fk_0018_it (fk_col) VALUES ('a');
INSERT INTO tc_tc_11_fk_0018_it (fk_col) VALUES ('a');
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0018_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(50) CHARACTER SET latin1, data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0018_it (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0018_it (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0018_it (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0018_it (fk_col) VALUES ('abc');
INSERT INTO t2_tc_11_fk_0018_it (fk_col) VALUES ('hello_world');
INSERT INTO t2_tc_11_fk_0018_it (fk_col) VALUES ('a');
SELECT 'TC-11-FK-0018-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0018_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0018_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0018_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0018_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0018_it a JOIN t2_tc_11_fk_0018_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0018-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0018_it' AND column_name='fk_col';
SELECT 'TC-11-FK-0018-IT#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0018_it' AND column_name='data';
SELECT 'TC-11-FK-0018-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0018_it' AND column_name='fk_col';

-- Test Case: TC-11-FK-0019-IP
-- FK Scenario: child, Algorithm: inplace
-- Type: VARCHAR(50) -> VARCHAR(100)
-- FK Transition: FK-VC
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=5 alter_sha=f3d83d5c7cd1
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0019_ip, tp_tc_11_fk_0019_ip, t2_tc_11_fk_0019_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0019_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0019_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0019_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0019_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0019_ip (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0019_ip (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0019_ip (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0019_ip (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0019_ip (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0019_ip (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0019_ip (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0019_ip (fk_col) VALUES ('abc');
-- ALTER child table only
ALTER TABLE tc_tc_11_fk_0019_ip MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=inplace;
INSERT INTO tp_tc_11_fk_0019_ip (fk_col) VALUES ('hello_world');
INSERT INTO tc_tc_11_fk_0019_ip (fk_col) VALUES ('hello_world');
INSERT INTO tp_tc_11_fk_0019_ip (fk_col) VALUES ('a');
INSERT INTO tc_tc_11_fk_0019_ip (fk_col) VALUES ('a');
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0019_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(100) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0019_ip (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0019_ip (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0019_ip (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0019_ip (fk_col) VALUES ('abc');
INSERT INTO t2_tc_11_fk_0019_ip (fk_col) VALUES ('hello_world');
INSERT INTO t2_tc_11_fk_0019_ip (fk_col) VALUES ('a');
SELECT 'TC-11-FK-0019-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0019_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0019_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0019_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0019_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0019_ip a JOIN t2_tc_11_fk_0019_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0019-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(100)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(100) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0019_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0019-IP#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0019_ip' AND column_name='data';
SELECT 'TC-11-FK-0019-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0019_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0019-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0019_ip_fk on tc_tc_11_fk_0019_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0019_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0019_ip_fk';

-- Test Case: TC-11-FK-0020-IP
-- FK Scenario: parent, Algorithm: inplace
-- Type: VARCHAR(50) -> VARCHAR(100)
-- FK Transition: FK-VC
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=5 alter_sha=3570ec023a8b
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0020_ip, tp_tc_11_fk_0020_ip, t2_tc_11_fk_0020_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0020_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0020_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0020_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0020_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0020_ip (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0020_ip (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0020_ip (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0020_ip (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0020_ip (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0020_ip (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0020_ip (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0020_ip (fk_col) VALUES ('abc');
-- ALTER parent table only
ALTER TABLE tp_tc_11_fk_0020_ip MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=inplace;
INSERT INTO tp_tc_11_fk_0020_ip (fk_col) VALUES ('hello_world');
INSERT INTO tc_tc_11_fk_0020_ip (fk_col) VALUES ('hello_world');
INSERT INTO tp_tc_11_fk_0020_ip (fk_col) VALUES ('a');
INSERT INTO tc_tc_11_fk_0020_ip (fk_col) VALUES ('a');
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0020_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(100) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0020_ip (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0020_ip (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0020_ip (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0020_ip (fk_col) VALUES ('abc');
INSERT INTO t2_tc_11_fk_0020_ip (fk_col) VALUES ('hello_world');
INSERT INTO t2_tc_11_fk_0020_ip (fk_col) VALUES ('a');
SELECT 'TC-11-FK-0020-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0020_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0020_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0020_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0020_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0020_ip a JOIN t2_tc_11_fk_0020_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0020-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0020_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0020-IP#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0020_ip' AND column_name='data';
SELECT 'TC-11-FK-0020-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(100)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(100) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0020_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0020-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0020_ip_fk on tc_tc_11_fk_0020_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0020_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0020_ip_fk';

-- Test Case: TC-11-FK-0021-IP
-- FK Scenario: both, Algorithm: inplace
-- Type: VARCHAR(50) -> VARCHAR(100)
-- FK Transition: FK-VC
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=5 alter_sha=aac2770610be alter_sha=883b057823d2
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0021_ip, tp_tc_11_fk_0021_ip, t2_tc_11_fk_0021_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0021_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0021_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0021_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0021_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0021_ip (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0021_ip (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0021_ip (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0021_ip (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0021_ip (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0021_ip (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0021_ip (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0021_ip (fk_col) VALUES ('abc');
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_11_fk_0021_ip MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=inplace;

ALTER TABLE tc_tc_11_fk_0021_ip MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=inplace;
INSERT INTO tp_tc_11_fk_0021_ip (fk_col) VALUES ('hello_world');
INSERT INTO tc_tc_11_fk_0021_ip (fk_col) VALUES ('hello_world');
INSERT INTO tp_tc_11_fk_0021_ip (fk_col) VALUES ('a');
INSERT INTO tc_tc_11_fk_0021_ip (fk_col) VALUES ('a');
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0021_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(100) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0021_ip (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0021_ip (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0021_ip (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0021_ip (fk_col) VALUES ('abc');
INSERT INTO t2_tc_11_fk_0021_ip (fk_col) VALUES ('hello_world');
INSERT INTO t2_tc_11_fk_0021_ip (fk_col) VALUES ('a');
SELECT 'TC-11-FK-0021-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0021_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0021_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0021_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0021_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0021_ip a JOIN t2_tc_11_fk_0021_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0021-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(100)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(100) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0021_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0021-IP#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0021_ip' AND column_name='data';
SELECT 'TC-11-FK-0021-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(100)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(100) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0021_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0021-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0021_ip_fk on tc_tc_11_fk_0021_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0021_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0021_ip_fk';

-- Test Case: TC-11-FK-0022-IP
-- FK Scenario: both_fkc0, Algorithm: inplace
-- Type: VARCHAR(50) -> VARCHAR(100)
-- FK Transition: FK-VC
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=5 alter_sha=30a908b44a21 alter_sha=5f52722c26a5
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0022_ip, tp_tc_11_fk_0022_ip, t2_tc_11_fk_0022_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0022_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0022_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0022_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0022_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0022_ip (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0022_ip (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0022_ip (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0022_ip (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0022_ip (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0022_ip (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0022_ip (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0022_ip (fk_col) VALUES ('abc');
-- 实测: foreign_key_checks=0 并不能绕过 errno 3780
SET foreign_key_checks=0;
-- ALTER parent with fk_checks=0
ALTER TABLE tp_tc_11_fk_0022_ip MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=inplace;

ALTER TABLE tc_tc_11_fk_0022_ip MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=inplace;
SET foreign_key_checks=1;
INSERT INTO tp_tc_11_fk_0022_ip (fk_col) VALUES ('hello_world');
INSERT INTO tc_tc_11_fk_0022_ip (fk_col) VALUES ('hello_world');
INSERT INTO tp_tc_11_fk_0022_ip (fk_col) VALUES ('a');
INSERT INTO tc_tc_11_fk_0022_ip (fk_col) VALUES ('a');
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0022_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(100) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0022_ip (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0022_ip (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0022_ip (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0022_ip (fk_col) VALUES ('abc');
INSERT INTO t2_tc_11_fk_0022_ip (fk_col) VALUES ('hello_world');
INSERT INTO t2_tc_11_fk_0022_ip (fk_col) VALUES ('a');
SELECT 'TC-11-FK-0022-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0022_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0022_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0022_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0022_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0022_ip a JOIN t2_tc_11_fk_0022_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0022-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(100)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(100) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0022_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0022-IP#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0022_ip' AND column_name='data';
SELECT 'TC-11-FK-0022-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(100)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(100) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0022_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0022-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0022_ip_fk on tc_tc_11_fk_0022_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0022_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0022_ip_fk';

-- Test Case: TC-11-FK-0023-IP
-- FK Scenario: both_drop_fk, Algorithm: inplace
-- Type: VARCHAR(50) -> VARCHAR(100)
-- FK Transition: FK-VC
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=5 alter_sha=907482b90153 alter_sha=e5101353cb1c
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0023_ip, tp_tc_11_fk_0023_ip, t2_tc_11_fk_0023_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0023_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0023_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0023_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0023_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0023_ip (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0023_ip (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0023_ip (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0023_ip (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0023_ip (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0023_ip (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0023_ip (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0023_ip (fk_col) VALUES ('abc');
-- 正确序列: DROP FOREIGN KEY -> 改两侧 -> ADD FOREIGN KEY
ALTER TABLE tc_tc_11_fk_0023_ip DROP FOREIGN KEY tc_11_fk_0023_ip_fk;
-- ALTER parent (FK 已摘除)
ALTER TABLE tp_tc_11_fk_0023_ip MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=inplace;

ALTER TABLE tc_tc_11_fk_0023_ip MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=inplace;
ALTER TABLE tc_tc_11_fk_0023_ip ADD CONSTRAINT tc_11_fk_0023_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0023_ip(fk_col);
INSERT INTO tp_tc_11_fk_0023_ip (fk_col) VALUES ('hello_world');
INSERT INTO tc_tc_11_fk_0023_ip (fk_col) VALUES ('hello_world');
INSERT INTO tp_tc_11_fk_0023_ip (fk_col) VALUES ('a');
INSERT INTO tc_tc_11_fk_0023_ip (fk_col) VALUES ('a');
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0023_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(100) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0023_ip (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0023_ip (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0023_ip (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0023_ip (fk_col) VALUES ('abc');
INSERT INTO t2_tc_11_fk_0023_ip (fk_col) VALUES ('hello_world');
INSERT INTO t2_tc_11_fk_0023_ip (fk_col) VALUES ('a');
SELECT 'TC-11-FK-0023-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0023_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0023_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0023_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0023_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0023_ip a JOIN t2_tc_11_fk_0023_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0023-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(100)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(100) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0023_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0023-IP#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(20) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0023_ip' AND column_name='data';
SELECT 'TC-11-FK-0023-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(100)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(100) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0023_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0023-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_11_fk_0023_ip_fk on tc_tc_11_fk_0023_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0023_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_11_fk_0023_ip_fk';

-- Test Case: TC-11-FK-0024-IP
-- FK Scenario: non_fk, Algorithm: inplace
-- Type: VARCHAR(50) -> VARCHAR(100)
-- FK Transition: FK-VC
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=4 alter_sha=78c2e3f861d1
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0024_ip, tp_tc_11_fk_0024_ip, t2_tc_11_fk_0024_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0024_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0024_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0024_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0024_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0024_ip (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0024_ip (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0024_ip (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0024_ip (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0024_ip (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0024_ip (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0024_ip (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0024_ip (fk_col) VALUES ('abc');
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_11_fk_0024_ip MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=inplace;
INSERT INTO tp_tc_11_fk_0024_ip (fk_col) VALUES ('hello_world');
INSERT INTO tc_tc_11_fk_0024_ip (fk_col) VALUES ('hello_world');
INSERT INTO tp_tc_11_fk_0024_ip (fk_col) VALUES ('a');
INSERT INTO tc_tc_11_fk_0024_ip (fk_col) VALUES ('a');
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0024_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(50) CHARACTER SET latin1, data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0024_ip (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0024_ip (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0024_ip (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0024_ip (fk_col) VALUES ('abc');
INSERT INTO t2_tc_11_fk_0024_ip (fk_col) VALUES ('hello_world');
INSERT INTO t2_tc_11_fk_0024_ip (fk_col) VALUES ('a');
SELECT 'TC-11-FK-0024-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0024_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0024_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0024_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0024_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0024_ip a JOIN t2_tc_11_fk_0024_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-11-FK-0024-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0024_ip' AND column_name='fk_col';
SELECT 'TC-11-FK-0024-IP#META_CHILD_DATA' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 1)
          AND 1=1
          AND 1=1
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=1 charset=* collation=* extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_11_fk_0024_ip' AND column_name='data';
SELECT 'TC-11-FK-0024-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(50)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(50) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_11_fk_0024_ip' AND column_name='fk_col';

