-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 内网环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: BINARY + VARBINARY + DECIMAL + TEXT + BLOB + BIT
-- 覆盖算法: INSTANT + INPLACE (增强类型 INSTANT 预期成功: BINARY/VARBINARY/DECIMAL 已确认支持)
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- Suite-Revision: 1186b16f779b   (生成器源码哈希; 时间戳见 results/generation_manifest.json)
-- 用例 ID 规则: TC-<文件号>-<作用域>-<序号>-<IT|IP>  —— 全局唯一
--   作用域 REG=普通表 OFAT/二元组, ATR=列属性保持, SPE=特殊模式,
--          FK=外键, PTK=分区(目标列是分区键), PNK=分区(目标列非分区键)
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

-- File 33: 秒级差分计时 (默认算法 vs 强制 COPY, 524288 行)

-- Test Case: TC-33-TMG-0001-XX
-- Timing: default-algorithm vs forced COPY, 524288 rows
-- Type: BINARY(10) -> BINARY(20), Algorithm: default_vs_copy, Expected: SUCCESS
-- Transition ID: BIN-01
-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=f2c2a67b465e column_type=binary(20)
DROP TABLE IF EXISTS t1_tc_33_tmg_0001_xx, t2_tc_33_tmg_0001_xx;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_33_tmg_0001_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target BINARY(10)) ENGINE=InnoDB;
INSERT INTO t1_tc_33_tmg_0001_xx (target) VALUES (0x00000000000000000000);
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
INSERT INTO t1_tc_33_tmg_0001_xx (target) SELECT target FROM t1_tc_33_tmg_0001_xx;
ANALYZE TABLE t1_tc_33_tmg_0001_xx;
CREATE TABLE t2_tc_33_tmg_0001_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target BINARY(10)) ENGINE=InnoDB;
INSERT INTO t2_tc_33_tmg_0001_xx (target) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
INSERT INTO t2_tc_33_tmg_0001_xx (target) SELECT target FROM t2_tc_33_tmg_0001_xx;
ANALYZE TABLE t2_tc_33_tmg_0001_xx;
SET @t0 = NOW(6);
ALTER TABLE t1_tc_33_tmg_0001_xx MODIFY target BINARY(20);
SET @t1 = NOW(6);
SET @t2 = NOW(6);
ALTER TABLE t2_tc_33_tmg_0001_xx MODIFY target BINARY(20), ALGORITHM=COPY;
SET @t3 = NOW(6);
SELECT 'TC-33-TMG-0001-XX#FAST_PATH' AS test_id,
       IF(TIMESTAMPDIFF(MICROSECOND,@t0,@t1) * 3 < TIMESTAMPDIFF(MICROSECOND,@t2,@t3)
          AND TIMESTAMPDIFF(MICROSECOND,@t0,@t1) < 2000000,'PASS','FAIL') AS result,
       CONCAT('default_us=',TIMESTAMPDIFF(MICROSECOND,@t0,@t1),' copy_us=',TIMESTAMPDIFF(MICROSECOND,@t2,@t3),' ratio=',ROUND(TIMESTAMPDIFF(MICROSECOND,@t2,@t3)/GREATEST(TIMESTAMPDIFF(MICROSECOND,@t0,@t1),1),1),' need_ratio>3 and default_us<2000000') AS mismatch;
SELECT 'TC-33-TMG-0001-XX#META' AS test_id,
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
              'want[type=binary(20) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_33_tmg_0001_xx' AND column_name='target';

-- Test Case: TC-33-TMG-0002-XX
-- Timing: default-algorithm vs forced COPY, 524288 rows
-- Type: VARBINARY(20) -> VARBINARY(40), Algorithm: default_vs_copy, Expected: SUCCESS
-- Transition ID: VBIN-01
-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=807387f53730 column_type=varbinary(40)
DROP TABLE IF EXISTS t1_tc_33_tmg_0002_xx, t2_tc_33_tmg_0002_xx;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_33_tmg_0002_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target VARBINARY(20)) ENGINE=InnoDB;
INSERT INTO t1_tc_33_tmg_0002_xx (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
INSERT INTO t1_tc_33_tmg_0002_xx (target) SELECT target FROM t1_tc_33_tmg_0002_xx;
ANALYZE TABLE t1_tc_33_tmg_0002_xx;
CREATE TABLE t2_tc_33_tmg_0002_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target VARBINARY(20)) ENGINE=InnoDB;
INSERT INTO t2_tc_33_tmg_0002_xx (target) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
INSERT INTO t2_tc_33_tmg_0002_xx (target) SELECT target FROM t2_tc_33_tmg_0002_xx;
ANALYZE TABLE t2_tc_33_tmg_0002_xx;
SET @t0 = NOW(6);
ALTER TABLE t1_tc_33_tmg_0002_xx MODIFY target VARBINARY(40);
SET @t1 = NOW(6);
SET @t2 = NOW(6);
ALTER TABLE t2_tc_33_tmg_0002_xx MODIFY target VARBINARY(40), ALGORITHM=COPY;
SET @t3 = NOW(6);
SELECT 'TC-33-TMG-0002-XX#FAST_PATH' AS test_id,
       IF(TIMESTAMPDIFF(MICROSECOND,@t0,@t1) * 3 < TIMESTAMPDIFF(MICROSECOND,@t2,@t3)
          AND TIMESTAMPDIFF(MICROSECOND,@t0,@t1) < 2000000,'PASS','FAIL') AS result,
       CONCAT('default_us=',TIMESTAMPDIFF(MICROSECOND,@t0,@t1),' copy_us=',TIMESTAMPDIFF(MICROSECOND,@t2,@t3),' ratio=',ROUND(TIMESTAMPDIFF(MICROSECOND,@t2,@t3)/GREATEST(TIMESTAMPDIFF(MICROSECOND,@t0,@t1),1),1),' need_ratio>3 and default_us<2000000') AS mismatch;
SELECT 'TC-33-TMG-0002-XX#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varbinary(40)'
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
              'want[type=varbinary(40) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_33_tmg_0002_xx' AND column_name='target';

-- Test Case: TC-33-TMG-0003-XX
-- Timing: default-algorithm vs forced COPY, 524288 rows
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default_vs_copy, Expected: SUCCESS
-- Transition ID: DEC-01
-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=d3ae76f1fda7 column_type=decimal(12,2)
DROP TABLE IF EXISTS t1_tc_33_tmg_0003_xx, t2_tc_33_tmg_0003_xx;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_33_tmg_0003_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target DECIMAL(10,2)) ENGINE=InnoDB;
INSERT INTO t1_tc_33_tmg_0003_xx (target) VALUES (-99999999.99);
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
INSERT INTO t1_tc_33_tmg_0003_xx (target) SELECT target FROM t1_tc_33_tmg_0003_xx;
ANALYZE TABLE t1_tc_33_tmg_0003_xx;
CREATE TABLE t2_tc_33_tmg_0003_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target DECIMAL(10,2)) ENGINE=InnoDB;
INSERT INTO t2_tc_33_tmg_0003_xx (target) VALUES (-99999999.99);
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
INSERT INTO t2_tc_33_tmg_0003_xx (target) SELECT target FROM t2_tc_33_tmg_0003_xx;
ANALYZE TABLE t2_tc_33_tmg_0003_xx;
SET @t0 = NOW(6);
ALTER TABLE t1_tc_33_tmg_0003_xx MODIFY target DECIMAL(12,2);
SET @t1 = NOW(6);
SET @t2 = NOW(6);
ALTER TABLE t2_tc_33_tmg_0003_xx MODIFY target DECIMAL(12,2), ALGORITHM=COPY;
SET @t3 = NOW(6);
SELECT 'TC-33-TMG-0003-XX#FAST_PATH' AS test_id,
       IF(TIMESTAMPDIFF(MICROSECOND,@t0,@t1) * 3 < TIMESTAMPDIFF(MICROSECOND,@t2,@t3)
          AND TIMESTAMPDIFF(MICROSECOND,@t0,@t1) < 2000000,'PASS','FAIL') AS result,
       CONCAT('default_us=',TIMESTAMPDIFF(MICROSECOND,@t0,@t1),' copy_us=',TIMESTAMPDIFF(MICROSECOND,@t2,@t3),' ratio=',ROUND(TIMESTAMPDIFF(MICROSECOND,@t2,@t3)/GREATEST(TIMESTAMPDIFF(MICROSECOND,@t0,@t1),1),1),' need_ratio>3 and default_us<2000000') AS mismatch;
SELECT 'TC-33-TMG-0003-XX#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(12,2)'
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
              'want[type=decimal(12,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_33_tmg_0003_xx' AND column_name='target';

-- Test Case: TC-33-TMG-0004-XX
-- Timing: default-algorithm vs forced COPY, 524288 rows
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: default_vs_copy, Expected: SUCCESS
-- Transition ID: DEC-04
-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=b4a835b97c83 column_type=decimal(65,30)
DROP TABLE IF EXISTS t1_tc_33_tmg_0004_xx, t2_tc_33_tmg_0004_xx;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_33_tmg_0004_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target DECIMAL(64,30)) ENGINE=InnoDB;
INSERT INTO t1_tc_33_tmg_0004_xx (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
INSERT INTO t1_tc_33_tmg_0004_xx (target) SELECT target FROM t1_tc_33_tmg_0004_xx;
ANALYZE TABLE t1_tc_33_tmg_0004_xx;
CREATE TABLE t2_tc_33_tmg_0004_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target DECIMAL(64,30)) ENGINE=InnoDB;
INSERT INTO t2_tc_33_tmg_0004_xx (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
INSERT INTO t2_tc_33_tmg_0004_xx (target) SELECT target FROM t2_tc_33_tmg_0004_xx;
ANALYZE TABLE t2_tc_33_tmg_0004_xx;
SET @t0 = NOW(6);
ALTER TABLE t1_tc_33_tmg_0004_xx MODIFY target DECIMAL(65,30);
SET @t1 = NOW(6);
SET @t2 = NOW(6);
ALTER TABLE t2_tc_33_tmg_0004_xx MODIFY target DECIMAL(65,30), ALGORITHM=COPY;
SET @t3 = NOW(6);
SELECT 'TC-33-TMG-0004-XX#FAST_PATH' AS test_id,
       IF(TIMESTAMPDIFF(MICROSECOND,@t0,@t1) * 3 < TIMESTAMPDIFF(MICROSECOND,@t2,@t3)
          AND TIMESTAMPDIFF(MICROSECOND,@t0,@t1) < 2000000,'PASS','FAIL') AS result,
       CONCAT('default_us=',TIMESTAMPDIFF(MICROSECOND,@t0,@t1),' copy_us=',TIMESTAMPDIFF(MICROSECOND,@t2,@t3),' ratio=',ROUND(TIMESTAMPDIFF(MICROSECOND,@t2,@t3)/GREATEST(TIMESTAMPDIFF(MICROSECOND,@t0,@t1),1),1),' need_ratio>3 and default_us<2000000') AS mismatch;
SELECT 'TC-33-TMG-0004-XX#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(65,30)'
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
              'want[type=decimal(65,30) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_33_tmg_0004_xx' AND column_name='target';

-- Test Case: TC-33-TMG-0005-XX
-- Timing: default-algorithm vs forced COPY, 524288 rows
-- Type: DECIMAL(64,0) -> DECIMAL(65,0), Algorithm: default_vs_copy, Expected: SUCCESS
-- Transition ID: DEC-07
-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=9c6cc7b1a7c2 column_type=decimal(65,0)
DROP TABLE IF EXISTS t1_tc_33_tmg_0005_xx, t2_tc_33_tmg_0005_xx;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_33_tmg_0005_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target DECIMAL(64,0)) ENGINE=InnoDB;
INSERT INTO t1_tc_33_tmg_0005_xx (target) VALUES (-9999999999999999999999999999999999999999999999999999999999999999);
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
INSERT INTO t1_tc_33_tmg_0005_xx (target) SELECT target FROM t1_tc_33_tmg_0005_xx;
ANALYZE TABLE t1_tc_33_tmg_0005_xx;
CREATE TABLE t2_tc_33_tmg_0005_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target DECIMAL(64,0)) ENGINE=InnoDB;
INSERT INTO t2_tc_33_tmg_0005_xx (target) VALUES (-9999999999999999999999999999999999999999999999999999999999999999);
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
INSERT INTO t2_tc_33_tmg_0005_xx (target) SELECT target FROM t2_tc_33_tmg_0005_xx;
ANALYZE TABLE t2_tc_33_tmg_0005_xx;
SET @t0 = NOW(6);
ALTER TABLE t1_tc_33_tmg_0005_xx MODIFY target DECIMAL(65,0);
SET @t1 = NOW(6);
SET @t2 = NOW(6);
ALTER TABLE t2_tc_33_tmg_0005_xx MODIFY target DECIMAL(65,0), ALGORITHM=COPY;
SET @t3 = NOW(6);
SELECT 'TC-33-TMG-0005-XX#FAST_PATH' AS test_id,
       IF(TIMESTAMPDIFF(MICROSECOND,@t0,@t1) * 3 < TIMESTAMPDIFF(MICROSECOND,@t2,@t3)
          AND TIMESTAMPDIFF(MICROSECOND,@t0,@t1) < 2000000,'PASS','FAIL') AS result,
       CONCAT('default_us=',TIMESTAMPDIFF(MICROSECOND,@t0,@t1),' copy_us=',TIMESTAMPDIFF(MICROSECOND,@t2,@t3),' ratio=',ROUND(TIMESTAMPDIFF(MICROSECOND,@t2,@t3)/GREATEST(TIMESTAMPDIFF(MICROSECOND,@t0,@t1),1),1),' need_ratio>3 and default_us<2000000') AS mismatch;
SELECT 'TC-33-TMG-0005-XX#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(65,0)'
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
              'want[type=decimal(65,0) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_33_tmg_0005_xx' AND column_name='target';

-- Test Case: TC-33-TMG-0006-XX
-- Timing: default-algorithm vs forced COPY, 524288 rows
-- Type: DECIMAL(17,2) -> DECIMAL(18,2), Algorithm: default_vs_copy, Expected: SUCCESS
-- Transition ID: DEC-10
-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=ae50677fa0a5 column_type=decimal(18,2)
DROP TABLE IF EXISTS t1_tc_33_tmg_0006_xx, t2_tc_33_tmg_0006_xx;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_33_tmg_0006_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target DECIMAL(17,2)) ENGINE=InnoDB;
INSERT INTO t1_tc_33_tmg_0006_xx (target) VALUES (-999999999999999.99);
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
INSERT INTO t1_tc_33_tmg_0006_xx (target) SELECT target FROM t1_tc_33_tmg_0006_xx;
ANALYZE TABLE t1_tc_33_tmg_0006_xx;
CREATE TABLE t2_tc_33_tmg_0006_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target DECIMAL(17,2)) ENGINE=InnoDB;
INSERT INTO t2_tc_33_tmg_0006_xx (target) VALUES (-999999999999999.99);
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
INSERT INTO t2_tc_33_tmg_0006_xx (target) SELECT target FROM t2_tc_33_tmg_0006_xx;
ANALYZE TABLE t2_tc_33_tmg_0006_xx;
SET @t0 = NOW(6);
ALTER TABLE t1_tc_33_tmg_0006_xx MODIFY target DECIMAL(18,2);
SET @t1 = NOW(6);
SET @t2 = NOW(6);
ALTER TABLE t2_tc_33_tmg_0006_xx MODIFY target DECIMAL(18,2), ALGORITHM=COPY;
SET @t3 = NOW(6);
SELECT 'TC-33-TMG-0006-XX#FAST_PATH' AS test_id,
       IF(TIMESTAMPDIFF(MICROSECOND,@t0,@t1) * 3 < TIMESTAMPDIFF(MICROSECOND,@t2,@t3)
          AND TIMESTAMPDIFF(MICROSECOND,@t0,@t1) < 2000000,'PASS','FAIL') AS result,
       CONCAT('default_us=',TIMESTAMPDIFF(MICROSECOND,@t0,@t1),' copy_us=',TIMESTAMPDIFF(MICROSECOND,@t2,@t3),' ratio=',ROUND(TIMESTAMPDIFF(MICROSECOND,@t2,@t3)/GREATEST(TIMESTAMPDIFF(MICROSECOND,@t0,@t1),1),1),' need_ratio>3 and default_us<2000000') AS mismatch;
SELECT 'TC-33-TMG-0006-XX#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(18,2)'
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
              'want[type=decimal(18,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_33_tmg_0006_xx' AND column_name='target';

-- Test Case: TC-33-TMG-0007-XX
-- Timing: default-algorithm vs forced COPY, 524288 rows
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default_vs_copy, Expected: SUCCESS
-- Transition ID: TEXT-02
-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=139d185e7208 column_type=mediumtext
DROP TABLE IF EXISTS t1_tc_33_tmg_0007_xx, t2_tc_33_tmg_0007_xx;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_33_tmg_0007_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target TEXT CHARACTER SET utf8mb4) ENGINE=InnoDB;
INSERT INTO t1_tc_33_tmg_0007_xx (target) VALUES ('');
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
INSERT INTO t1_tc_33_tmg_0007_xx (target) SELECT target FROM t1_tc_33_tmg_0007_xx;
ANALYZE TABLE t1_tc_33_tmg_0007_xx;
CREATE TABLE t2_tc_33_tmg_0007_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target TEXT CHARACTER SET utf8mb4) ENGINE=InnoDB;
INSERT INTO t2_tc_33_tmg_0007_xx (target) VALUES ('');
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
INSERT INTO t2_tc_33_tmg_0007_xx (target) SELECT target FROM t2_tc_33_tmg_0007_xx;
ANALYZE TABLE t2_tc_33_tmg_0007_xx;
SET @t0 = NOW(6);
ALTER TABLE t1_tc_33_tmg_0007_xx MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SET @t1 = NOW(6);
SET @t2 = NOW(6);
ALTER TABLE t2_tc_33_tmg_0007_xx MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=COPY;
SET @t3 = NOW(6);
SELECT 'TC-33-TMG-0007-XX#FAST_PATH' AS test_id,
       IF(TIMESTAMPDIFF(MICROSECOND,@t0,@t1) * 3 < TIMESTAMPDIFF(MICROSECOND,@t2,@t3)
          AND TIMESTAMPDIFF(MICROSECOND,@t0,@t1) < 2000000,'PASS','FAIL') AS result,
       CONCAT('default_us=',TIMESTAMPDIFF(MICROSECOND,@t0,@t1),' copy_us=',TIMESTAMPDIFF(MICROSECOND,@t2,@t3),' ratio=',ROUND(TIMESTAMPDIFF(MICROSECOND,@t2,@t3)/GREATEST(TIMESTAMPDIFF(MICROSECOND,@t0,@t1),1),1),' need_ratio>3 and default_us<2000000') AS mismatch;
SELECT 'TC-33-TMG-0007-XX#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='mediumtext'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'utf8mb4')
          AND (MAX(collation_name) <=> 'utf8mb4_0900_ai_ci')
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
              'want[type=mediumtext nullable=YES has_default=0 charset=utf8mb4 collation=utf8mb4_0900_ai_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_33_tmg_0007_xx' AND column_name='target';

-- Test Case: TC-33-TMG-0008-XX
-- Timing: default-algorithm vs forced COPY, 524288 rows
-- Type: BLOB -> MEDIUMBLOB, Algorithm: default_vs_copy, Expected: SUCCESS
-- Transition ID: BLOB-02
-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=f76d2c8f2bfa column_type=mediumblob
DROP TABLE IF EXISTS t1_tc_33_tmg_0008_xx, t2_tc_33_tmg_0008_xx;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_33_tmg_0008_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target BLOB) ENGINE=InnoDB;
INSERT INTO t1_tc_33_tmg_0008_xx (target) VALUES ('');
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
INSERT INTO t1_tc_33_tmg_0008_xx (target) SELECT target FROM t1_tc_33_tmg_0008_xx;
ANALYZE TABLE t1_tc_33_tmg_0008_xx;
CREATE TABLE t2_tc_33_tmg_0008_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target BLOB) ENGINE=InnoDB;
INSERT INTO t2_tc_33_tmg_0008_xx (target) VALUES ('');
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
INSERT INTO t2_tc_33_tmg_0008_xx (target) SELECT target FROM t2_tc_33_tmg_0008_xx;
ANALYZE TABLE t2_tc_33_tmg_0008_xx;
SET @t0 = NOW(6);
ALTER TABLE t1_tc_33_tmg_0008_xx MODIFY target MEDIUMBLOB;
SET @t1 = NOW(6);
SET @t2 = NOW(6);
ALTER TABLE t2_tc_33_tmg_0008_xx MODIFY target MEDIUMBLOB, ALGORITHM=COPY;
SET @t3 = NOW(6);
SELECT 'TC-33-TMG-0008-XX#FAST_PATH' AS test_id,
       IF(TIMESTAMPDIFF(MICROSECOND,@t0,@t1) * 3 < TIMESTAMPDIFF(MICROSECOND,@t2,@t3)
          AND TIMESTAMPDIFF(MICROSECOND,@t0,@t1) < 2000000,'PASS','FAIL') AS result,
       CONCAT('default_us=',TIMESTAMPDIFF(MICROSECOND,@t0,@t1),' copy_us=',TIMESTAMPDIFF(MICROSECOND,@t2,@t3),' ratio=',ROUND(TIMESTAMPDIFF(MICROSECOND,@t2,@t3)/GREATEST(TIMESTAMPDIFF(MICROSECOND,@t0,@t1),1),1),' need_ratio>3 and default_us<2000000') AS mismatch;
SELECT 'TC-33-TMG-0008-XX#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='mediumblob'
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
              'want[type=mediumblob nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_33_tmg_0008_xx' AND column_name='target';

