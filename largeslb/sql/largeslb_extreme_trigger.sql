-- ============================================================
-- LargeSLB 极致触发 SQL 脚本
-- 用途：手动验证 LargeSLB 分拆路径是否可达
-- 目标：在单 Slice 上累积 > 2MB redo，触发 TLB 分拆
-- ============================================================
--
-- 前置条件（必须执行）：
--   SET GLOBAL enable_large_slb = 1;
--   SET GLOBAL innodb_log_write_max_size = 524288;
--   SET GLOBAL innodb_log_write_min_time_interval = 1000000;
--   SET GLOBAL innodb_log_write_min_size = 131072;
--
-- 观察指标：
--   SHOW STATUS LIKE 'large_mtr';        -- 应 > 0
--   SHOW STATUS LIKE 'large_mtr_size';   -- 应 > 2097152 (2MB)
--
-- ============================================================

-- 方式1: 同行热点 — 最可靠，1行更新96次，所有redo到同page-id
-- 预估 redo: 96 × 32KB ≈ 3MB，全部到同一个 Slice

DROP PROCEDURE IF EXISTS lslb_extreme_same_page_hot;
DELIMITER //
CREATE PROCEDURE lslb_extreme_same_page_hot()
BEGIN
    DECLARE i INT DEFAULT 0;

    -- 建表
    DROP TABLE IF EXISTS lslb_extreme_hot;
    CREATE TABLE lslb_extreme_hot (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        data LONGTEXT
    ) ENGINE=InnoDB;

    -- 插入1行种子
    INSERT INTO lslb_extreme_hot (data) VALUES (REPEAT('H', 32768));

    -- 同一行反复更新 96 次，每次写入 32KB
    -- 所有 redo 记录属于同一 page_id → 同一 Slice → 累积 > 2MB
    WHILE i < 96 DO
        UPDATE lslb_extreme_hot SET data = REPEAT(CONCAT('X', i), 32768) WHERE id = 1;
        SET i = i + 1;
    END WHILE;

    SELECT COUNT(*) AS total_updates FROM lslb_extreme_hot;
END //
DELIMITER ;

-- 执行
CALL lslb_extreme_same_page_hot();

-- 检查是否触发
-- SHOW STATUS LIKE 'large_mtr';


-- ============================================================
-- 方式2: 单桶大 payload 批量更新 — 160行 × 32KB ≈ 5MB
-- ============================================================

DROP PROCEDURE IF EXISTS lslb_extreme_large_single_bucket;
DELIMITER //
CREATE PROCEDURE lslb_extreme_large_single_bucket()
BEGIN
    DECLARE i INT DEFAULT 0;

    DROP TABLE IF EXISTS lslb_extreme_bucket;
    CREATE TABLE lslb_extreme_bucket (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        bucket_id INT NOT NULL,
        data LONGTEXT
    ) ENGINE=InnoDB;

    -- 插入 160 行到同一个桶（bucket_id=0）
    WHILE i < 160 DO
        INSERT INTO lslb_extreme_bucket (bucket_id, data) VALUES (0, REPEAT('S', 8192));
        SET i = i + 1;
    END WHILE;

    -- 单次事务：一次 UPDATE 160 行，每行写入 32KB payload
    -- 预估 redo: 160 × 32KB ≈ 5MB → 同一桶的行大概率映射到同一 Slice
    START TRANSACTION;
    UPDATE lslb_extreme_bucket
        SET data = REPEAT('U', 32768)
        WHERE bucket_id = 0;
    COMMIT;

    SELECT COUNT(*) AS updated_rows, SUM(OCTET_LENGTH(data)) AS total_bytes
        FROM lslb_extreme_bucket WHERE bucket_id = 0;
END //
DELIMITER ;

-- 执行
CALL lslb_extreme_large_single_bucket();

-- 检查是否触发
-- SHOW STATUS LIKE 'large_mtr';


-- ============================================================
-- 方式3: 多批次累积 — 同桶连续3次大批量 UPDATE
-- 每次 128行 × 16KB ≈ 2MB，3次在同一个 flush session 累积 ≈ 6MB
-- ============================================================

DROP PROCEDURE IF EXISTS lslb_extreme_multi_batch;
DELIMITER //
CREATE PROCEDURE lslb_extreme_multi_batch()
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE batch INT DEFAULT 0;

    DROP TABLE IF EXISTS lslb_extreme_batch;
    CREATE TABLE lslb_extreme_batch (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        bucket_id INT NOT NULL,
        data LONGTEXT
    ) ENGINE=InnoDB;

    -- 插入 384 行到桶0
    WHILE i < 384 DO
        INSERT INTO lslb_extreme_batch (bucket_id, data) VALUES (0, REPEAT('B', 8192));
        SET i = i + 1;
    END WHILE;

    -- 3 批次连续更新，每批 128 行 × 16KB payload
    -- 依赖延迟刷盘让 3 批次在同一个 flush session 累积
    WHILE batch < 3 DO
        START TRANSACTION;
        UPDATE lslb_extreme_batch
            SET data = REPEAT(CONCAT('M', batch), 16384)
            WHERE bucket_id = 0
            LIMIT 128;
        COMMIT;
        -- 不sleep，紧接下一批次，最大化 flush session 内累积
        SET batch = batch + 1;
    END WHILE;

    SELECT COUNT(*) AS total_rows, SUM(OCTET_LENGTH(data)) AS total_bytes
        FROM lslb_extreme_batch WHERE bucket_id = 0;
END //
DELIMITER ;

-- 执行
CALL lslb_extreme_multi_batch();

-- 检查是否触发
-- SHOW STATUS LIKE 'large_mtr';


-- ============================================================
-- 方式4: 2MB 精确边界 — 513行 × 4KB = 2MB + 4KB（刚过边界）
-- ============================================================

DROP PROCEDURE IF EXISTS lslb_extreme_boundary_2m;
DELIMITER //
CREATE PROCEDURE lslb_extreme_boundary_2m()
BEGIN
    DECLARE i INT DEFAULT 0;

    DROP TABLE IF EXISTS lslb_extreme_boundary;
    CREATE TABLE lslb_extreme_boundary (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        data VARCHAR(16383)
    ) ENGINE=InnoDB;

    -- 插入 513 行
    WHILE i < 513 DO
        INSERT INTO lslb_extreme_boundary (data) VALUES (REPEAT('D', 4096));
        SET i = i + 1;
    END WHILE;

    -- 一次事务更新全部 513 行 × 4KB
    -- 513 × 4096 = 2,101,248 bytes ≈ 2MB + 4KB（刚超过 2MB 边界）
    START TRANSACTION;
    UPDATE lslb_extreme_boundary SET data = REPEAT('E', 4096);
    COMMIT;

    SELECT COUNT(*) AS rows_updated, SUM(OCTET_LENGTH(data)) AS total_bytes,
        SUM(OCTET_LENGTH(data)) / 1048576.0 AS total_mb
        FROM lslb_extreme_boundary;
END //
DELIMITER ;

-- 执行
CALL lslb_extreme_boundary_2m();

-- 检查是否触发
-- SHOW STATUS LIKE 'large_mtr';


-- ============================================================
-- 方式5: LONGBLOB 极致 — 96 行 × 1MB payload ≈ 96MB redo
-- 二进制大字段，最大化 redo 量
-- ============================================================

DROP PROCEDURE IF EXISTS lslb_extreme_blob_max;
DELIMITER //
CREATE PROCEDURE lslb_extreme_blob_max()
BEGIN
    DECLARE i INT DEFAULT 0;

    DROP TABLE IF EXISTS lslb_extreme_blob;
    CREATE TABLE lslb_extreme_blob (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        data LONGBLOB
    ) ENGINE=InnoDB;

    -- 插入 96 行，每行 256KB 种子数据
    WHILE i < 96 DO
        INSERT INTO lslb_extreme_blob (data) VALUES (REPEAT(BINARY 'Y', 262144));
        SET i = i + 1;
    END WHILE;

    -- 一次事务更新 96 行，每行写入 1MB payload
    -- 96 × 1MB ≈ 96MB redo → 每个包含这些行的 Slice 必定 > 2MB
    START TRANSACTION;
    UPDATE lslb_extreme_blob SET data = REPEAT(BINARY 'Z', 1048576);
    COMMIT;

    SELECT COUNT(*) AS rows_updated, SUM(OCTET_LENGTH(data)) AS total_bytes,
        SUM(OCTET_LENGTH(data)) / 1048576.0 AS total_mb
        FROM lslb_extreme_blob;
END //
DELIMITER ;

-- 执行
CALL lslb_extreme_blob_max();

-- 检查是否触发
-- SHOW STATUS LIKE 'large_mtr';
