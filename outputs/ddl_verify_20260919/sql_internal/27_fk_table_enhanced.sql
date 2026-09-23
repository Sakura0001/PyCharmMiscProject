-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 内网环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: BINARY + VARBINARY + DECIMAL + TEXT + BLOB + BIT
-- 覆盖算法: INSTANT + INPLACE (增强类型 INSTANT 预期成功: BINARY/VARBINARY/DECIMAL 已确认支持)
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- Suite-Revision: fe94a870b930   (生成器源码哈希; 时间戳见 results/generation_manifest.json)
-- 用例 ID 规则: TC-<文件号>-<作用域>-<序号>-<IT|IP>  —— 全局唯一
--   作用域 REG=普通表 OFAT/二元组, ATR=列属性保持, SPE=特殊模式,
--          FK=外键, PTK=分区(目标列是分区键), PNK=分区(目标列非分区键)
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

-- File 27: 外键表测试(增强类型)

-- Test Case: TC-27-FK-0001-IT
-- FK Scenario: child, Algorithm: instant
-- Type: BINARY(10) -> BINARY(20)
-- FK Transition: FK-BIN
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845] build=SUCCESS assertions=5 alter_sha=ae43685246de
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0001_it, tp_tc_27_fk_0001_it, t2_tc_27_fk_0001_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0001_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0001_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0001_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0001_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0001_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0001_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0001_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0001_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0001_it (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0001_it (fk_col) VALUES (0x41424142414241424142);
-- ALTER child table only
ALTER TABLE tc_tc_27_fk_0001_it MODIFY fk_col BINARY(20), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0001_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0001_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0001_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0001_it (fk_col) VALUES (0x41424142414241424142);
SELECT 'TC-27-FK-0001-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0001_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0001_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0001_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0001_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0001_it a JOIN t2_tc_27_fk_0001_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0001-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(10)'
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
              ' want[type=binary(10) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0001_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0001-IT#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0001_it' AND column_name='data';
SELECT 'TC-27-FK-0001-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(10)'
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
              ' want[type=binary(10) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0001_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0001-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0001_it_fk on tc_tc_27_fk_0001_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0001_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0001_it_fk';

-- Test Case: TC-27-FK-0002-IT
-- FK Scenario: parent, Algorithm: instant
-- Type: BINARY(10) -> BINARY(20)
-- FK Transition: FK-BIN
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845] build=SUCCESS assertions=5 alter_sha=b9212aacbccb
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0002_it, tp_tc_27_fk_0002_it, t2_tc_27_fk_0002_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0002_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0002_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0002_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0002_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0002_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0002_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0002_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0002_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0002_it (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0002_it (fk_col) VALUES (0x41424142414241424142);
-- ALTER parent table only
ALTER TABLE tp_tc_27_fk_0002_it MODIFY fk_col BINARY(20), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0002_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0002_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0002_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0002_it (fk_col) VALUES (0x41424142414241424142);
SELECT 'TC-27-FK-0002-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0002_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0002_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0002_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0002_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0002_it a JOIN t2_tc_27_fk_0002_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0002-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(10)'
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
              ' want[type=binary(10) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0002_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0002-IT#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0002_it' AND column_name='data';
SELECT 'TC-27-FK-0002-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(10)'
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
              ' want[type=binary(10) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0002_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0002-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0002_it_fk on tc_tc_27_fk_0002_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0002_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0002_it_fk';

-- Test Case: TC-27-FK-0003-IT
-- FK Scenario: both, Algorithm: instant
-- Type: BINARY(10) -> BINARY(20)
-- FK Transition: FK-BIN
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845] build=SUCCESS assertions=5 alter_sha=f1d0c07d2fb0 alter_sha=5e057665bd3b
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0003_it, tp_tc_27_fk_0003_it, t2_tc_27_fk_0003_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0003_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0003_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0003_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0003_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0003_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0003_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0003_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0003_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0003_it (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0003_it (fk_col) VALUES (0x41424142414241424142);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_27_fk_0003_it MODIFY fk_col BINARY(20), ALGORITHM=instant;

ALTER TABLE tc_tc_27_fk_0003_it MODIFY fk_col BINARY(20), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0003_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0003_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0003_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0003_it (fk_col) VALUES (0x41424142414241424142);
SELECT 'TC-27-FK-0003-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0003_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0003_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0003_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0003_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0003_it a JOIN t2_tc_27_fk_0003_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0003-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(10)'
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
              ' want[type=binary(10) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0003_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0003-IT#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0003_it' AND column_name='data';
SELECT 'TC-27-FK-0003-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(10)'
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
              ' want[type=binary(10) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0003_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0003-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0003_it_fk on tc_tc_27_fk_0003_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0003_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0003_it_fk';

-- Test Case: TC-27-FK-0004-IT
-- FK Scenario: both_fkc0, Algorithm: instant
-- Type: BINARY(10) -> BINARY(20)
-- FK Transition: FK-BIN
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845] build=SUCCESS assertions=5 alter_sha=20b64e7cf7cc alter_sha=b1bd4d4c1b84
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0004_it, tp_tc_27_fk_0004_it, t2_tc_27_fk_0004_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0004_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0004_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0004_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0004_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0004_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0004_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0004_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0004_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0004_it (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0004_it (fk_col) VALUES (0x41424142414241424142);
-- 实测: foreign_key_checks=0 并不能绕过 errno 3780
SET foreign_key_checks=0;
-- ALTER parent with fk_checks=0
ALTER TABLE tp_tc_27_fk_0004_it MODIFY fk_col BINARY(20), ALGORITHM=instant;

ALTER TABLE tc_tc_27_fk_0004_it MODIFY fk_col BINARY(20), ALGORITHM=instant;
SET foreign_key_checks=1;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0004_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0004_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0004_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0004_it (fk_col) VALUES (0x41424142414241424142);
SELECT 'TC-27-FK-0004-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0004_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0004_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0004_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0004_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0004_it a JOIN t2_tc_27_fk_0004_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0004-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(10)'
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
              ' want[type=binary(10) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0004_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0004-IT#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0004_it' AND column_name='data';
SELECT 'TC-27-FK-0004-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(10)'
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
              ' want[type=binary(10) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0004_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0004-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0004_it_fk on tc_tc_27_fk_0004_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0004_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0004_it_fk';

-- Test Case: TC-27-FK-0005-IT
-- FK Scenario: both_drop_fk, Algorithm: instant
-- Type: BINARY(10) -> BINARY(20)
-- FK Transition: FK-BIN
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845] build=SUCCESS assertions=5 alter_sha=684c635bf548 alter_sha=c57aad0b90e6
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0005_it, tp_tc_27_fk_0005_it, t2_tc_27_fk_0005_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0005_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0005_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0005_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0005_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0005_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0005_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0005_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0005_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0005_it (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0005_it (fk_col) VALUES (0x41424142414241424142);
-- 正确序列: DROP FOREIGN KEY -> 改两侧 -> ADD FOREIGN KEY
ALTER TABLE tc_tc_27_fk_0005_it DROP FOREIGN KEY tc_27_fk_0005_it_fk;
-- ALTER parent (FK 已摘除)
ALTER TABLE tp_tc_27_fk_0005_it MODIFY fk_col BINARY(20), ALGORITHM=instant;

ALTER TABLE tc_tc_27_fk_0005_it MODIFY fk_col BINARY(20), ALGORITHM=instant;
ALTER TABLE tc_tc_27_fk_0005_it ADD CONSTRAINT tc_27_fk_0005_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0005_it(fk_col);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0005_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0005_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0005_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0005_it (fk_col) VALUES (0x41424142414241424142);
SELECT 'TC-27-FK-0005-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0005_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0005_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0005_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0005_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0005_it a JOIN t2_tc_27_fk_0005_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0005-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(10)'
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
              ' want[type=binary(10) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0005_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0005-IT#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0005_it' AND column_name='data';
SELECT 'TC-27-FK-0005-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(10)'
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
              ' want[type=binary(10) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0005_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0005-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0005_it_fk on tc_tc_27_fk_0005_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0005_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0005_it_fk';

-- Test Case: TC-27-FK-0006-IT
-- FK Scenario: non_fk, Algorithm: instant
-- Type: BINARY(10) -> BINARY(20)
-- FK Transition: FK-BIN
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845,1846] build=SUCCESS assertions=4 alter_sha=d545fa3ac816
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0006_it, tp_tc_27_fk_0006_it, t2_tc_27_fk_0006_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0006_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0006_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0006_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0006_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0006_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0006_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0006_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0006_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0006_it (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0006_it (fk_col) VALUES (0x41424142414241424142);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_27_fk_0006_it MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0006_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0006_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0006_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0006_it (fk_col) VALUES (0x41424142414241424142);
SELECT 'TC-27-FK-0006-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0006_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0006_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0006_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0006_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0006_it a JOIN t2_tc_27_fk_0006_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0006-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(10)'
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
              ' want[type=binary(10) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0006_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0006-IT#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0006_it' AND column_name='data';
SELECT 'TC-27-FK-0006-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(10)'
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
              ' want[type=binary(10) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0006_it' AND column_name='fk_col';

-- Test Case: TC-27-FK-0007-IP
-- FK Scenario: child, Algorithm: inplace
-- Type: BINARY(10) -> BINARY(20)
-- FK Transition: FK-BIN
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=5 alter_sha=0e4ca65d6644
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0007_ip, tp_tc_27_fk_0007_ip, t2_tc_27_fk_0007_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0007_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0007_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0007_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0007_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0007_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0007_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0007_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0007_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0007_ip (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0007_ip (fk_col) VALUES (0x41424142414241424142);
-- ALTER child table only
ALTER TABLE tc_tc_27_fk_0007_ip MODIFY fk_col BINARY(20), ALGORITHM=inplace;
INSERT INTO tp_tc_27_fk_0007_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0007_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0007_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0007_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0007_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(20), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0007_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0007_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0007_ip (fk_col) VALUES (0x41424142414241424142);
INSERT INTO t2_tc_27_fk_0007_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0007_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-27-FK-0007-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0007_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0007_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0007_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0007_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0007_ip a JOIN t2_tc_27_fk_0007_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0007-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(20)'
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
              ' want[type=binary(20) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0007_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0007-IP#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0007_ip' AND column_name='data';
SELECT 'TC-27-FK-0007-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(10)'
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
              ' want[type=binary(10) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0007_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0007-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0007_ip_fk on tc_tc_27_fk_0007_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0007_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0007_ip_fk';

-- Test Case: TC-27-FK-0008-IP
-- FK Scenario: parent, Algorithm: inplace
-- Type: BINARY(10) -> BINARY(20)
-- FK Transition: FK-BIN
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=5 alter_sha=194f3bf0d113
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0008_ip, tp_tc_27_fk_0008_ip, t2_tc_27_fk_0008_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0008_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0008_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0008_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0008_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0008_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0008_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0008_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0008_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0008_ip (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0008_ip (fk_col) VALUES (0x41424142414241424142);
-- ALTER parent table only
ALTER TABLE tp_tc_27_fk_0008_ip MODIFY fk_col BINARY(20), ALGORITHM=inplace;
INSERT INTO tp_tc_27_fk_0008_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0008_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0008_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0008_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0008_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(20), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0008_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0008_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0008_ip (fk_col) VALUES (0x41424142414241424142);
INSERT INTO t2_tc_27_fk_0008_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0008_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-27-FK-0008-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0008_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0008_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0008_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0008_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0008_ip a JOIN t2_tc_27_fk_0008_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0008-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(10)'
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
              ' want[type=binary(10) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0008_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0008-IP#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0008_ip' AND column_name='data';
SELECT 'TC-27-FK-0008-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(20)'
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
              ' want[type=binary(20) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0008_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0008-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0008_ip_fk on tc_tc_27_fk_0008_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0008_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0008_ip_fk';

-- Test Case: TC-27-FK-0009-IP
-- FK Scenario: both, Algorithm: inplace
-- Type: BINARY(10) -> BINARY(20)
-- FK Transition: FK-BIN
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=5 alter_sha=191b482b4577 alter_sha=7f743cf1e72b
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0009_ip, tp_tc_27_fk_0009_ip, t2_tc_27_fk_0009_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0009_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0009_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0009_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0009_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0009_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0009_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0009_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0009_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0009_ip (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0009_ip (fk_col) VALUES (0x41424142414241424142);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_27_fk_0009_ip MODIFY fk_col BINARY(20), ALGORITHM=inplace;

ALTER TABLE tc_tc_27_fk_0009_ip MODIFY fk_col BINARY(20), ALGORITHM=inplace;
INSERT INTO tp_tc_27_fk_0009_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0009_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0009_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0009_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0009_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(20), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0009_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0009_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0009_ip (fk_col) VALUES (0x41424142414241424142);
INSERT INTO t2_tc_27_fk_0009_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0009_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-27-FK-0009-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0009_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0009_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0009_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0009_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0009_ip a JOIN t2_tc_27_fk_0009_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0009-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(20)'
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
              ' want[type=binary(20) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0009_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0009-IP#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0009_ip' AND column_name='data';
SELECT 'TC-27-FK-0009-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(20)'
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
              ' want[type=binary(20) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0009_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0009-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0009_ip_fk on tc_tc_27_fk_0009_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0009_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0009_ip_fk';

-- Test Case: TC-27-FK-0010-IP
-- FK Scenario: both_fkc0, Algorithm: inplace
-- Type: BINARY(10) -> BINARY(20)
-- FK Transition: FK-BIN
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=5 alter_sha=978a73b14ddd alter_sha=659d1c6fb186
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0010_ip, tp_tc_27_fk_0010_ip, t2_tc_27_fk_0010_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0010_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0010_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0010_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0010_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0010_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0010_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0010_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0010_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0010_ip (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0010_ip (fk_col) VALUES (0x41424142414241424142);
-- 实测: foreign_key_checks=0 并不能绕过 errno 3780
SET foreign_key_checks=0;
-- ALTER parent with fk_checks=0
ALTER TABLE tp_tc_27_fk_0010_ip MODIFY fk_col BINARY(20), ALGORITHM=inplace;

ALTER TABLE tc_tc_27_fk_0010_ip MODIFY fk_col BINARY(20), ALGORITHM=inplace;
SET foreign_key_checks=1;
INSERT INTO tp_tc_27_fk_0010_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0010_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0010_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0010_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0010_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(20), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0010_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0010_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0010_ip (fk_col) VALUES (0x41424142414241424142);
INSERT INTO t2_tc_27_fk_0010_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0010_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-27-FK-0010-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0010_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0010_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0010_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0010_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0010_ip a JOIN t2_tc_27_fk_0010_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0010-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(20)'
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
              ' want[type=binary(20) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0010_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0010-IP#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0010_ip' AND column_name='data';
SELECT 'TC-27-FK-0010-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(20)'
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
              ' want[type=binary(20) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0010_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0010-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0010_ip_fk on tc_tc_27_fk_0010_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0010_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0010_ip_fk';

-- Test Case: TC-27-FK-0011-IP
-- FK Scenario: both_drop_fk, Algorithm: inplace
-- Type: BINARY(10) -> BINARY(20)
-- FK Transition: FK-BIN
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=5 alter_sha=2fa79eba3b3f alter_sha=cdf71413ac6a
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0011_ip, tp_tc_27_fk_0011_ip, t2_tc_27_fk_0011_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0011_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0011_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0011_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0011_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0011_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0011_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0011_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0011_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0011_ip (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0011_ip (fk_col) VALUES (0x41424142414241424142);
-- 正确序列: DROP FOREIGN KEY -> 改两侧 -> ADD FOREIGN KEY
ALTER TABLE tc_tc_27_fk_0011_ip DROP FOREIGN KEY tc_27_fk_0011_ip_fk;
-- ALTER parent (FK 已摘除)
ALTER TABLE tp_tc_27_fk_0011_ip MODIFY fk_col BINARY(20), ALGORITHM=inplace;

ALTER TABLE tc_tc_27_fk_0011_ip MODIFY fk_col BINARY(20), ALGORITHM=inplace;
ALTER TABLE tc_tc_27_fk_0011_ip ADD CONSTRAINT tc_27_fk_0011_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0011_ip(fk_col);
INSERT INTO tp_tc_27_fk_0011_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0011_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0011_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0011_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0011_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(20), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0011_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0011_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0011_ip (fk_col) VALUES (0x41424142414241424142);
INSERT INTO t2_tc_27_fk_0011_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0011_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-27-FK-0011-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0011_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0011_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0011_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0011_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0011_ip a JOIN t2_tc_27_fk_0011_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0011-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(20)'
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
              ' want[type=binary(20) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0011_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0011-IP#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0011_ip' AND column_name='data';
SELECT 'TC-27-FK-0011-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(20)'
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
              ' want[type=binary(20) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0011_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0011-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0011_ip_fk on tc_tc_27_fk_0011_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0011_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0011_ip_fk';

-- Test Case: TC-27-FK-0012-IP
-- FK Scenario: non_fk, Algorithm: inplace
-- Type: BINARY(10) -> BINARY(20)
-- FK Transition: FK-BIN
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=4 alter_sha=82b017a4efd9
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0012_ip, tp_tc_27_fk_0012_ip, t2_tc_27_fk_0012_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0012_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0012_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0012_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0012_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0012_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0012_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0012_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0012_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0012_ip (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0012_ip (fk_col) VALUES (0x41424142414241424142);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_27_fk_0012_ip MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=inplace;
INSERT INTO tp_tc_27_fk_0012_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0012_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0012_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0012_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0012_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0012_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0012_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0012_ip (fk_col) VALUES (0x41424142414241424142);
INSERT INTO t2_tc_27_fk_0012_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0012_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-27-FK-0012-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0012_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0012_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0012_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0012_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0012_ip a JOIN t2_tc_27_fk_0012_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0012-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(10)'
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
              ' want[type=binary(10) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0012_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0012-IP#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0012_ip' AND column_name='data';
SELECT 'TC-27-FK-0012-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(10)'
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
              ' want[type=binary(10) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0012_ip' AND column_name='fk_col';

-- Test Case: TC-27-FK-0013-IT
-- FK Scenario: child, Algorithm: instant
-- Type: VARBINARY(50) -> VARBINARY(100)
-- FK Transition: FK-VBIN
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845] build=SUCCESS assertions=5 alter_sha=38df37285372
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0013_it, tp_tc_27_fk_0013_it, t2_tc_27_fk_0013_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0013_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0013_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0013_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0013_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0013_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0013_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0013_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0013_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER child table only
ALTER TABLE tc_tc_27_fk_0013_it MODIFY fk_col VARBINARY(100), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0013_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(50), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0013_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0013_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-27-FK-0013-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0013_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0013_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0013_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0013_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0013_it a JOIN t2_tc_27_fk_0013_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0013-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(50)'
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
              ' want[type=varbinary(50) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0013_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0013-IT#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0013_it' AND column_name='data';
SELECT 'TC-27-FK-0013-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(50)'
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
              ' want[type=varbinary(50) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0013_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0013-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0013_it_fk on tc_tc_27_fk_0013_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0013_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0013_it_fk';

-- Test Case: TC-27-FK-0014-IT
-- FK Scenario: parent, Algorithm: instant
-- Type: VARBINARY(50) -> VARBINARY(100)
-- FK Transition: FK-VBIN
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845] build=SUCCESS assertions=5 alter_sha=e64fdc974f3a
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0014_it, tp_tc_27_fk_0014_it, t2_tc_27_fk_0014_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0014_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0014_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0014_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0014_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0014_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0014_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0014_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0014_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER parent table only
ALTER TABLE tp_tc_27_fk_0014_it MODIFY fk_col VARBINARY(100), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0014_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(50), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0014_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0014_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-27-FK-0014-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0014_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0014_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0014_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0014_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0014_it a JOIN t2_tc_27_fk_0014_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0014-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(50)'
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
              ' want[type=varbinary(50) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0014_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0014-IT#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0014_it' AND column_name='data';
SELECT 'TC-27-FK-0014-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(50)'
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
              ' want[type=varbinary(50) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0014_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0014-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0014_it_fk on tc_tc_27_fk_0014_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0014_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0014_it_fk';

-- Test Case: TC-27-FK-0015-IT
-- FK Scenario: both, Algorithm: instant
-- Type: VARBINARY(50) -> VARBINARY(100)
-- FK Transition: FK-VBIN
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845] build=SUCCESS assertions=5 alter_sha=fd1e01577055 alter_sha=d59d12b9ab23
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0015_it, tp_tc_27_fk_0015_it, t2_tc_27_fk_0015_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0015_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0015_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0015_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0015_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0015_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0015_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0015_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0015_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_27_fk_0015_it MODIFY fk_col VARBINARY(100), ALGORITHM=instant;

ALTER TABLE tc_tc_27_fk_0015_it MODIFY fk_col VARBINARY(100), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0015_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(50), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0015_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0015_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-27-FK-0015-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0015_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0015_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0015_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0015_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0015_it a JOIN t2_tc_27_fk_0015_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0015-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(50)'
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
              ' want[type=varbinary(50) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0015_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0015-IT#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0015_it' AND column_name='data';
SELECT 'TC-27-FK-0015-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(50)'
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
              ' want[type=varbinary(50) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0015_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0015-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0015_it_fk on tc_tc_27_fk_0015_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0015_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0015_it_fk';

-- Test Case: TC-27-FK-0016-IT
-- FK Scenario: both_fkc0, Algorithm: instant
-- Type: VARBINARY(50) -> VARBINARY(100)
-- FK Transition: FK-VBIN
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845] build=SUCCESS assertions=5 alter_sha=db2953b3e101 alter_sha=6c01c4f514d3
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0016_it, tp_tc_27_fk_0016_it, t2_tc_27_fk_0016_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0016_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0016_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0016_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0016_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0016_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0016_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0016_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0016_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- 实测: foreign_key_checks=0 并不能绕过 errno 3780
SET foreign_key_checks=0;
-- ALTER parent with fk_checks=0
ALTER TABLE tp_tc_27_fk_0016_it MODIFY fk_col VARBINARY(100), ALGORITHM=instant;

ALTER TABLE tc_tc_27_fk_0016_it MODIFY fk_col VARBINARY(100), ALGORITHM=instant;
SET foreign_key_checks=1;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0016_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(50), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0016_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0016_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-27-FK-0016-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0016_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0016_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0016_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0016_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0016_it a JOIN t2_tc_27_fk_0016_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0016-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(50)'
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
              ' want[type=varbinary(50) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0016_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0016-IT#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0016_it' AND column_name='data';
SELECT 'TC-27-FK-0016-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(50)'
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
              ' want[type=varbinary(50) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0016_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0016-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0016_it_fk on tc_tc_27_fk_0016_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0016_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0016_it_fk';

-- Test Case: TC-27-FK-0017-IT
-- FK Scenario: both_drop_fk, Algorithm: instant
-- Type: VARBINARY(50) -> VARBINARY(100)
-- FK Transition: FK-VBIN
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845] build=SUCCESS assertions=5 alter_sha=fc74866e0f43 alter_sha=529a60f8b678
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0017_it, tp_tc_27_fk_0017_it, t2_tc_27_fk_0017_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0017_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0017_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0017_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0017_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0017_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0017_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0017_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0017_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- 正确序列: DROP FOREIGN KEY -> 改两侧 -> ADD FOREIGN KEY
ALTER TABLE tc_tc_27_fk_0017_it DROP FOREIGN KEY tc_27_fk_0017_it_fk;
-- ALTER parent (FK 已摘除)
ALTER TABLE tp_tc_27_fk_0017_it MODIFY fk_col VARBINARY(100), ALGORITHM=instant;

ALTER TABLE tc_tc_27_fk_0017_it MODIFY fk_col VARBINARY(100), ALGORITHM=instant;
ALTER TABLE tc_tc_27_fk_0017_it ADD CONSTRAINT tc_27_fk_0017_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0017_it(fk_col);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0017_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(50), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0017_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0017_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-27-FK-0017-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0017_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0017_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0017_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0017_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0017_it a JOIN t2_tc_27_fk_0017_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0017-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(50)'
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
              ' want[type=varbinary(50) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0017_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0017-IT#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0017_it' AND column_name='data';
SELECT 'TC-27-FK-0017-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(50)'
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
              ' want[type=varbinary(50) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0017_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0017-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0017_it_fk on tc_tc_27_fk_0017_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0017_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0017_it_fk';

-- Test Case: TC-27-FK-0018-IT
-- FK Scenario: non_fk, Algorithm: instant
-- Type: VARBINARY(50) -> VARBINARY(100)
-- FK Transition: FK-VBIN
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845,1846] build=SUCCESS assertions=4 alter_sha=7fb9c050eab2
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0018_it, tp_tc_27_fk_0018_it, t2_tc_27_fk_0018_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0018_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0018_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0018_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0018_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0018_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0018_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0018_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0018_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_27_fk_0018_it MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0018_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(50), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0018_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0018_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-27-FK-0018-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0018_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0018_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0018_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0018_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0018_it a JOIN t2_tc_27_fk_0018_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0018-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(50)'
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
              ' want[type=varbinary(50) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0018_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0018-IT#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0018_it' AND column_name='data';
SELECT 'TC-27-FK-0018-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(50)'
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
              ' want[type=varbinary(50) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0018_it' AND column_name='fk_col';

-- Test Case: TC-27-FK-0019-IP
-- FK Scenario: child, Algorithm: inplace
-- Type: VARBINARY(50) -> VARBINARY(100)
-- FK Transition: FK-VBIN
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=5 alter_sha=5b8d657ae694
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0019_ip, tp_tc_27_fk_0019_ip, t2_tc_27_fk_0019_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0019_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0019_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0019_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0019_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0019_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0019_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0019_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0019_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER child table only
ALTER TABLE tc_tc_27_fk_0019_ip MODIFY fk_col VARBINARY(100), ALGORITHM=inplace;
INSERT INTO tp_tc_27_fk_0019_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0019_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0019_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(100), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0019_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0019_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0019_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
SELECT 'TC-27-FK-0019-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0019_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0019_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0019_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0019_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0019_ip a JOIN t2_tc_27_fk_0019_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0019-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(100)'
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
              ' want[type=varbinary(100) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0019_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0019-IP#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0019_ip' AND column_name='data';
SELECT 'TC-27-FK-0019-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(50)'
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
              ' want[type=varbinary(50) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0019_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0019-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0019_ip_fk on tc_tc_27_fk_0019_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0019_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0019_ip_fk';

-- Test Case: TC-27-FK-0020-IP
-- FK Scenario: parent, Algorithm: inplace
-- Type: VARBINARY(50) -> VARBINARY(100)
-- FK Transition: FK-VBIN
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=5 alter_sha=21e15647b87d
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0020_ip, tp_tc_27_fk_0020_ip, t2_tc_27_fk_0020_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0020_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0020_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0020_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0020_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0020_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0020_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0020_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0020_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER parent table only
ALTER TABLE tp_tc_27_fk_0020_ip MODIFY fk_col VARBINARY(100), ALGORITHM=inplace;
INSERT INTO tp_tc_27_fk_0020_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0020_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0020_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(100), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0020_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0020_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0020_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
SELECT 'TC-27-FK-0020-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0020_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0020_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0020_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0020_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0020_ip a JOIN t2_tc_27_fk_0020_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0020-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(50)'
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
              ' want[type=varbinary(50) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0020_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0020-IP#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0020_ip' AND column_name='data';
SELECT 'TC-27-FK-0020-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(100)'
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
              ' want[type=varbinary(100) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0020_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0020-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0020_ip_fk on tc_tc_27_fk_0020_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0020_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0020_ip_fk';

-- Test Case: TC-27-FK-0021-IP
-- FK Scenario: both, Algorithm: inplace
-- Type: VARBINARY(50) -> VARBINARY(100)
-- FK Transition: FK-VBIN
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=5 alter_sha=2f0a0ef084c0 alter_sha=f957ba5630ab
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0021_ip, tp_tc_27_fk_0021_ip, t2_tc_27_fk_0021_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0021_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0021_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0021_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0021_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0021_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0021_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0021_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0021_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_27_fk_0021_ip MODIFY fk_col VARBINARY(100), ALGORITHM=inplace;

ALTER TABLE tc_tc_27_fk_0021_ip MODIFY fk_col VARBINARY(100), ALGORITHM=inplace;
INSERT INTO tp_tc_27_fk_0021_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0021_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0021_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(100), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0021_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0021_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0021_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
SELECT 'TC-27-FK-0021-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0021_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0021_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0021_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0021_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0021_ip a JOIN t2_tc_27_fk_0021_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0021-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(100)'
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
              ' want[type=varbinary(100) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0021_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0021-IP#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0021_ip' AND column_name='data';
SELECT 'TC-27-FK-0021-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(100)'
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
              ' want[type=varbinary(100) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0021_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0021-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0021_ip_fk on tc_tc_27_fk_0021_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0021_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0021_ip_fk';

-- Test Case: TC-27-FK-0022-IP
-- FK Scenario: both_fkc0, Algorithm: inplace
-- Type: VARBINARY(50) -> VARBINARY(100)
-- FK Transition: FK-VBIN
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=5 alter_sha=c77721b78f24 alter_sha=bd2e4ca0b851
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0022_ip, tp_tc_27_fk_0022_ip, t2_tc_27_fk_0022_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0022_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0022_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0022_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0022_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0022_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0022_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0022_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0022_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- 实测: foreign_key_checks=0 并不能绕过 errno 3780
SET foreign_key_checks=0;
-- ALTER parent with fk_checks=0
ALTER TABLE tp_tc_27_fk_0022_ip MODIFY fk_col VARBINARY(100), ALGORITHM=inplace;

ALTER TABLE tc_tc_27_fk_0022_ip MODIFY fk_col VARBINARY(100), ALGORITHM=inplace;
SET foreign_key_checks=1;
INSERT INTO tp_tc_27_fk_0022_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0022_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0022_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(100), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0022_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0022_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0022_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
SELECT 'TC-27-FK-0022-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0022_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0022_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0022_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0022_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0022_ip a JOIN t2_tc_27_fk_0022_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0022-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(100)'
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
              ' want[type=varbinary(100) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0022_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0022-IP#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0022_ip' AND column_name='data';
SELECT 'TC-27-FK-0022-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(100)'
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
              ' want[type=varbinary(100) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0022_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0022-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0022_ip_fk on tc_tc_27_fk_0022_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0022_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0022_ip_fk';

-- Test Case: TC-27-FK-0023-IP
-- FK Scenario: both_drop_fk, Algorithm: inplace
-- Type: VARBINARY(50) -> VARBINARY(100)
-- FK Transition: FK-VBIN
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=5 alter_sha=54cd63bcf05a alter_sha=5a5a22c1c93a
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0023_ip, tp_tc_27_fk_0023_ip, t2_tc_27_fk_0023_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0023_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0023_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0023_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0023_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0023_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0023_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0023_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0023_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- 正确序列: DROP FOREIGN KEY -> 改两侧 -> ADD FOREIGN KEY
ALTER TABLE tc_tc_27_fk_0023_ip DROP FOREIGN KEY tc_27_fk_0023_ip_fk;
-- ALTER parent (FK 已摘除)
ALTER TABLE tp_tc_27_fk_0023_ip MODIFY fk_col VARBINARY(100), ALGORITHM=inplace;

ALTER TABLE tc_tc_27_fk_0023_ip MODIFY fk_col VARBINARY(100), ALGORITHM=inplace;
ALTER TABLE tc_tc_27_fk_0023_ip ADD CONSTRAINT tc_27_fk_0023_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0023_ip(fk_col);
INSERT INTO tp_tc_27_fk_0023_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0023_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0023_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(100), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0023_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0023_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0023_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
SELECT 'TC-27-FK-0023-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0023_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0023_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0023_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0023_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0023_ip a JOIN t2_tc_27_fk_0023_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0023-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(100)'
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
              ' want[type=varbinary(100) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0023_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0023-IP#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0023_ip' AND column_name='data';
SELECT 'TC-27-FK-0023-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(100)'
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
              ' want[type=varbinary(100) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0023_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0023-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0023_ip_fk on tc_tc_27_fk_0023_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0023_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0023_ip_fk';

-- Test Case: TC-27-FK-0024-IP
-- FK Scenario: non_fk, Algorithm: inplace
-- Type: VARBINARY(50) -> VARBINARY(100)
-- FK Transition: FK-VBIN
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=4 alter_sha=24ec83b0f417
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0024_ip, tp_tc_27_fk_0024_ip, t2_tc_27_fk_0024_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0024_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0024_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0024_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0024_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0024_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0024_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0024_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0024_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_27_fk_0024_ip MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=inplace;
INSERT INTO tp_tc_27_fk_0024_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0024_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0024_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(50), data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0024_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0024_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0024_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
SELECT 'TC-27-FK-0024-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0024_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0024_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0024_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0024_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0024_ip a JOIN t2_tc_27_fk_0024_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0024-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(50)'
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
              ' want[type=varbinary(50) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0024_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0024-IP#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0024_ip' AND column_name='data';
SELECT 'TC-27-FK-0024-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(50)'
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
              ' want[type=varbinary(50) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0024_ip' AND column_name='fk_col';

-- Test Case: TC-27-FK-0025-IT
-- FK Scenario: child, Algorithm: instant
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- FK Transition: FK-DEC
-- Expected: FAIL
-- @expect alter=FAIL errno=[1846] build=SUCCESS assertions=5 alter_sha=5d22b0ffbbe4
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0025_it, tp_tc_27_fk_0025_it, t2_tc_27_fk_0025_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0025_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0025_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0025_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0025_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0025_it (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0025_it (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0025_it (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0025_it (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0025_it (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0025_it (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0025_it (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0025_it (fk_col) VALUES (99.99);
-- ALTER child table only
ALTER TABLE tc_tc_27_fk_0025_it MODIFY fk_col DECIMAL(12,2), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0025_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0025_it (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0025_it (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0025_it (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0025_it (fk_col) VALUES (99.99);
SELECT 'TC-27-FK-0025-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0025_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0025_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0025_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0025_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0025_it a JOIN t2_tc_27_fk_0025_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0025-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0025_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0025-IT#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0025_it' AND column_name='data';
SELECT 'TC-27-FK-0025-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0025_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0025-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0025_it_fk on tc_tc_27_fk_0025_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0025_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0025_it_fk';

-- Test Case: TC-27-FK-0026-IT
-- FK Scenario: parent, Algorithm: instant
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- FK Transition: FK-DEC
-- Expected: FAIL
-- @expect alter=FAIL errno=[1846] build=SUCCESS assertions=5 alter_sha=bf64c7afed10
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0026_it, tp_tc_27_fk_0026_it, t2_tc_27_fk_0026_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0026_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0026_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0026_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0026_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0026_it (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0026_it (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0026_it (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0026_it (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0026_it (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0026_it (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0026_it (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0026_it (fk_col) VALUES (99.99);
-- ALTER parent table only
ALTER TABLE tp_tc_27_fk_0026_it MODIFY fk_col DECIMAL(12,2), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0026_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0026_it (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0026_it (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0026_it (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0026_it (fk_col) VALUES (99.99);
SELECT 'TC-27-FK-0026-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0026_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0026_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0026_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0026_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0026_it a JOIN t2_tc_27_fk_0026_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0026-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0026_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0026-IT#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0026_it' AND column_name='data';
SELECT 'TC-27-FK-0026-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0026_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0026-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0026_it_fk on tc_tc_27_fk_0026_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0026_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0026_it_fk';

-- Test Case: TC-27-FK-0027-IT
-- FK Scenario: both, Algorithm: instant
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- FK Transition: FK-DEC
-- Expected: FAIL
-- @expect alter=FAIL errno=[1846] build=SUCCESS assertions=5 alter_sha=e11015dc2524 alter_sha=af0157158b93
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0027_it, tp_tc_27_fk_0027_it, t2_tc_27_fk_0027_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0027_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0027_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0027_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0027_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0027_it (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0027_it (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0027_it (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0027_it (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0027_it (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0027_it (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0027_it (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0027_it (fk_col) VALUES (99.99);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_27_fk_0027_it MODIFY fk_col DECIMAL(12,2), ALGORITHM=instant;

ALTER TABLE tc_tc_27_fk_0027_it MODIFY fk_col DECIMAL(12,2), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0027_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0027_it (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0027_it (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0027_it (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0027_it (fk_col) VALUES (99.99);
SELECT 'TC-27-FK-0027-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0027_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0027_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0027_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0027_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0027_it a JOIN t2_tc_27_fk_0027_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0027-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0027_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0027-IT#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0027_it' AND column_name='data';
SELECT 'TC-27-FK-0027-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0027_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0027-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0027_it_fk on tc_tc_27_fk_0027_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0027_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0027_it_fk';

-- Test Case: TC-27-FK-0028-IT
-- FK Scenario: both_fkc0, Algorithm: instant
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- FK Transition: FK-DEC
-- Expected: FAIL
-- @expect alter=FAIL errno=[1846] build=SUCCESS assertions=5 alter_sha=d3b40c871f04 alter_sha=c73fe0b93f5c
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0028_it, tp_tc_27_fk_0028_it, t2_tc_27_fk_0028_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0028_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0028_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0028_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0028_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0028_it (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0028_it (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0028_it (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0028_it (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0028_it (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0028_it (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0028_it (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0028_it (fk_col) VALUES (99.99);
-- 实测: foreign_key_checks=0 并不能绕过 errno 3780
SET foreign_key_checks=0;
-- ALTER parent with fk_checks=0
ALTER TABLE tp_tc_27_fk_0028_it MODIFY fk_col DECIMAL(12,2), ALGORITHM=instant;

ALTER TABLE tc_tc_27_fk_0028_it MODIFY fk_col DECIMAL(12,2), ALGORITHM=instant;
SET foreign_key_checks=1;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0028_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0028_it (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0028_it (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0028_it (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0028_it (fk_col) VALUES (99.99);
SELECT 'TC-27-FK-0028-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0028_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0028_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0028_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0028_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0028_it a JOIN t2_tc_27_fk_0028_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0028-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0028_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0028-IT#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0028_it' AND column_name='data';
SELECT 'TC-27-FK-0028-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0028_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0028-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0028_it_fk on tc_tc_27_fk_0028_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0028_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0028_it_fk';

-- Test Case: TC-27-FK-0029-IT
-- FK Scenario: both_drop_fk, Algorithm: instant
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- FK Transition: FK-DEC
-- Expected: FAIL
-- @expect alter=FAIL errno=[1846] build=SUCCESS assertions=5 alter_sha=51a765e922fd alter_sha=8a0f2610cb8e
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0029_it, tp_tc_27_fk_0029_it, t2_tc_27_fk_0029_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0029_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0029_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0029_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0029_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0029_it (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0029_it (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0029_it (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0029_it (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0029_it (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0029_it (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0029_it (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0029_it (fk_col) VALUES (99.99);
-- 正确序列: DROP FOREIGN KEY -> 改两侧 -> ADD FOREIGN KEY
ALTER TABLE tc_tc_27_fk_0029_it DROP FOREIGN KEY tc_27_fk_0029_it_fk;
-- ALTER parent (FK 已摘除)
ALTER TABLE tp_tc_27_fk_0029_it MODIFY fk_col DECIMAL(12,2), ALGORITHM=instant;

ALTER TABLE tc_tc_27_fk_0029_it MODIFY fk_col DECIMAL(12,2), ALGORITHM=instant;
ALTER TABLE tc_tc_27_fk_0029_it ADD CONSTRAINT tc_27_fk_0029_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0029_it(fk_col);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0029_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0029_it (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0029_it (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0029_it (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0029_it (fk_col) VALUES (99.99);
SELECT 'TC-27-FK-0029-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0029_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0029_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0029_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0029_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0029_it a JOIN t2_tc_27_fk_0029_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0029-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0029_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0029-IT#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0029_it' AND column_name='data';
SELECT 'TC-27-FK-0029-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0029_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0029-IT#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0029_it_fk on tc_tc_27_fk_0029_it: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0029_it' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0029_it_fk';

-- Test Case: TC-27-FK-0030-IT
-- FK Scenario: non_fk, Algorithm: instant
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- FK Transition: FK-DEC
-- Expected: FAIL
-- @expect alter=FAIL errno=[1845,1846] build=SUCCESS assertions=4 alter_sha=f56ee124d6b0
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0030_it, tp_tc_27_fk_0030_it, t2_tc_27_fk_0030_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0030_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0030_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0030_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0030_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0030_it (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0030_it (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0030_it (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0030_it (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0030_it (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0030_it (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0030_it (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0030_it (fk_col) VALUES (99.99);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_27_fk_0030_it MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0030_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0030_it (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0030_it (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0030_it (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0030_it (fk_col) VALUES (99.99);
SELECT 'TC-27-FK-0030-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0030_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0030_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0030_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0030_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0030_it a JOIN t2_tc_27_fk_0030_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0030-IT#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0030_it' AND column_name='fk_col';
SELECT 'TC-27-FK-0030-IT#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0030_it' AND column_name='data';
SELECT 'TC-27-FK-0030-IT#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0030_it' AND column_name='fk_col';

-- Test Case: TC-27-FK-0031-IP
-- FK Scenario: child, Algorithm: inplace
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- FK Transition: FK-DEC
-- Expected: FAIL
-- @expect alter=FAIL errno=[1846] build=SUCCESS assertions=5 alter_sha=089bbb4523de
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0031_ip, tp_tc_27_fk_0031_ip, t2_tc_27_fk_0031_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0031_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0031_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0031_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0031_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0031_ip (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0031_ip (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0031_ip (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0031_ip (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0031_ip (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0031_ip (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0031_ip (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0031_ip (fk_col) VALUES (99.99);
-- ALTER child table only
ALTER TABLE tc_tc_27_fk_0031_ip MODIFY fk_col DECIMAL(12,2), ALGORITHM=inplace;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0031_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0031_ip (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0031_ip (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0031_ip (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0031_ip (fk_col) VALUES (99.99);
SELECT 'TC-27-FK-0031-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0031_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0031_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0031_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0031_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0031_ip a JOIN t2_tc_27_fk_0031_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0031-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0031_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0031-IP#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0031_ip' AND column_name='data';
SELECT 'TC-27-FK-0031-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0031_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0031-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0031_ip_fk on tc_tc_27_fk_0031_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0031_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0031_ip_fk';

-- Test Case: TC-27-FK-0032-IP
-- FK Scenario: parent, Algorithm: inplace
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- FK Transition: FK-DEC
-- Expected: FAIL
-- @expect alter=FAIL errno=[1846] build=SUCCESS assertions=5 alter_sha=836f4103b876
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0032_ip, tp_tc_27_fk_0032_ip, t2_tc_27_fk_0032_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0032_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0032_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0032_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0032_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0032_ip (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0032_ip (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0032_ip (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0032_ip (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0032_ip (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0032_ip (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0032_ip (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0032_ip (fk_col) VALUES (99.99);
-- ALTER parent table only
ALTER TABLE tp_tc_27_fk_0032_ip MODIFY fk_col DECIMAL(12,2), ALGORITHM=inplace;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0032_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0032_ip (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0032_ip (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0032_ip (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0032_ip (fk_col) VALUES (99.99);
SELECT 'TC-27-FK-0032-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0032_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0032_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0032_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0032_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0032_ip a JOIN t2_tc_27_fk_0032_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0032-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0032_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0032-IP#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0032_ip' AND column_name='data';
SELECT 'TC-27-FK-0032-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0032_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0032-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0032_ip_fk on tc_tc_27_fk_0032_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0032_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0032_ip_fk';

-- Test Case: TC-27-FK-0033-IP
-- FK Scenario: both, Algorithm: inplace
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- FK Transition: FK-DEC
-- Expected: FAIL
-- @expect alter=FAIL errno=[1846] build=SUCCESS assertions=5 alter_sha=54247a3792d1 alter_sha=00266de068f5
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0033_ip, tp_tc_27_fk_0033_ip, t2_tc_27_fk_0033_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0033_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0033_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0033_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0033_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0033_ip (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0033_ip (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0033_ip (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0033_ip (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0033_ip (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0033_ip (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0033_ip (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0033_ip (fk_col) VALUES (99.99);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_27_fk_0033_ip MODIFY fk_col DECIMAL(12,2), ALGORITHM=inplace;

ALTER TABLE tc_tc_27_fk_0033_ip MODIFY fk_col DECIMAL(12,2), ALGORITHM=inplace;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0033_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0033_ip (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0033_ip (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0033_ip (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0033_ip (fk_col) VALUES (99.99);
SELECT 'TC-27-FK-0033-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0033_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0033_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0033_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0033_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0033_ip a JOIN t2_tc_27_fk_0033_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0033-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0033_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0033-IP#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0033_ip' AND column_name='data';
SELECT 'TC-27-FK-0033-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0033_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0033-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0033_ip_fk on tc_tc_27_fk_0033_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0033_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0033_ip_fk';

-- Test Case: TC-27-FK-0034-IP
-- FK Scenario: both_fkc0, Algorithm: inplace
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- FK Transition: FK-DEC
-- Expected: FAIL
-- @expect alter=FAIL errno=[1846] build=SUCCESS assertions=5 alter_sha=d365f05c3d29 alter_sha=50c565c79567
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0034_ip, tp_tc_27_fk_0034_ip, t2_tc_27_fk_0034_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0034_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0034_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0034_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0034_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0034_ip (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0034_ip (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0034_ip (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0034_ip (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0034_ip (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0034_ip (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0034_ip (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0034_ip (fk_col) VALUES (99.99);
-- 实测: foreign_key_checks=0 并不能绕过 errno 3780
SET foreign_key_checks=0;
-- ALTER parent with fk_checks=0
ALTER TABLE tp_tc_27_fk_0034_ip MODIFY fk_col DECIMAL(12,2), ALGORITHM=inplace;

ALTER TABLE tc_tc_27_fk_0034_ip MODIFY fk_col DECIMAL(12,2), ALGORITHM=inplace;
SET foreign_key_checks=1;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0034_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0034_ip (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0034_ip (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0034_ip (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0034_ip (fk_col) VALUES (99.99);
SELECT 'TC-27-FK-0034-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0034_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0034_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0034_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0034_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0034_ip a JOIN t2_tc_27_fk_0034_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0034-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0034_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0034-IP#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0034_ip' AND column_name='data';
SELECT 'TC-27-FK-0034-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0034_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0034-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0034_ip_fk on tc_tc_27_fk_0034_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0034_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0034_ip_fk';

-- Test Case: TC-27-FK-0035-IP
-- FK Scenario: both_drop_fk, Algorithm: inplace
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- FK Transition: FK-DEC
-- Expected: FAIL
-- @expect alter=FAIL errno=[1846] build=SUCCESS assertions=5 alter_sha=55d6d448bce0 alter_sha=b2c67fb61aeb
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0035_ip, tp_tc_27_fk_0035_ip, t2_tc_27_fk_0035_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0035_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0035_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0035_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0035_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0035_ip (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0035_ip (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0035_ip (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0035_ip (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0035_ip (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0035_ip (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0035_ip (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0035_ip (fk_col) VALUES (99.99);
-- 正确序列: DROP FOREIGN KEY -> 改两侧 -> ADD FOREIGN KEY
ALTER TABLE tc_tc_27_fk_0035_ip DROP FOREIGN KEY tc_27_fk_0035_ip_fk;
-- ALTER parent (FK 已摘除)
ALTER TABLE tp_tc_27_fk_0035_ip MODIFY fk_col DECIMAL(12,2), ALGORITHM=inplace;

ALTER TABLE tc_tc_27_fk_0035_ip MODIFY fk_col DECIMAL(12,2), ALGORITHM=inplace;
ALTER TABLE tc_tc_27_fk_0035_ip ADD CONSTRAINT tc_27_fk_0035_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0035_ip(fk_col);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0035_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0035_ip (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0035_ip (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0035_ip (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0035_ip (fk_col) VALUES (99.99);
SELECT 'TC-27-FK-0035-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0035_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0035_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0035_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0035_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0035_ip a JOIN t2_tc_27_fk_0035_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0035-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0035_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0035-IP#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0035_ip' AND column_name='data';
SELECT 'TC-27-FK-0035-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0035_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0035-IP#FK_CONSTRAINT_PRESENT' AS test_id,
       IF(COUNT(*)=1,'PASS','FAIL') AS result,
       CONCAT('foreign key tc_27_fk_0035_ip_fk on tc_tc_27_fk_0035_ip: found=',COUNT(*)) AS mismatch
FROM information_schema.table_constraints
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0035_ip' AND constraint_type='FOREIGN KEY'
  AND constraint_name='tc_27_fk_0035_ip_fk';

-- Test Case: TC-27-FK-0036-IP
-- FK Scenario: non_fk, Algorithm: inplace
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- FK Transition: FK-DEC
-- Expected: SUCCESS
-- @expect alter=SUCCESS build=SUCCESS assertions=4 alter_sha=db1c88483bd9
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0036_ip, tp_tc_27_fk_0036_ip, t2_tc_27_fk_0036_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0036_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0036_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0036_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0036_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0036_ip (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0036_ip (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0036_ip (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0036_ip (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0036_ip (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0036_ip (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0036_ip (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0036_ip (fk_col) VALUES (99.99);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_27_fk_0036_ip MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=inplace;
INSERT INTO tp_tc_27_fk_0036_ip (fk_col) VALUES (999.99);
INSERT INTO tc_tc_27_fk_0036_ip (fk_col) VALUES (999.99);
INSERT INTO tp_tc_27_fk_0036_ip (fk_col) VALUES (1000.00);
INSERT INTO tc_tc_27_fk_0036_ip (fk_col) VALUES (1000.00);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0036_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0036_ip (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0036_ip (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0036_ip (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0036_ip (fk_col) VALUES (99.99);
INSERT INTO t2_tc_27_fk_0036_ip (fk_col) VALUES (999.99);
INSERT INTO t2_tc_27_fk_0036_ip (fk_col) VALUES (1000.00);
SELECT 'TC-27-FK-0036-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0036_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0036_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0036_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0036_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0036_ip a JOIN t2_tc_27_fk_0036_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;
SELECT 'TC-27-FK-0036-IP#META_CHILD_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0036_ip' AND column_name='fk_col';
SELECT 'TC-27-FK-0036-IP#META_CHILD_DATA' AS test_id,
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
WHERE table_schema=DATABASE() AND table_name='tc_tc_27_fk_0036_ip' AND column_name='data';
SELECT 'TC-27-FK-0036-IP#META_PARENT_FK' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(10,2)'
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
              ' want[type=decimal(10,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='tp_tc_27_fk_0036_ip' AND column_name='fk_col';

