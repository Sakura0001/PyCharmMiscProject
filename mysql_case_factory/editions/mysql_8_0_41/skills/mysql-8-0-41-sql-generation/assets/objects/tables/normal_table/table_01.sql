-- object_key: normal_table
-- aliases: normal table,普通表,base table
DROP TABLE IF EXISTS {table_name};
CREATE TABLE {table_name}
(
    id_col BIGINT NOT NULL AUTO_INCREMENT,
    tinyint_col TINYINT,
    smallint_col SMALLINT,
    mediumint_col MEDIUMINT,
    int_col INT,
    bigint_col BIGINT,
    decimal_col DECIMAL(16,4),
    float_col FLOAT,
    double_col DOUBLE,
    bit_col BIT(8),
    char_col CHAR(20),
    varchar_col VARCHAR(100),
    binary_col BINARY(8),
    varbinary_col VARBINARY(32),
    text_col TEXT,
    longtext_col LONGTEXT,
    blob_col BLOB,
    enum_col ENUM('red','green','blue'),
    set_col SET('a','b','c'),
    date_col DATE,
    time_col TIME,
    datetime_col DATETIME,
    timestamp_col TIMESTAMP NULL,
    year_col YEAR,
    json_col JSON,
    point_col POINT NOT NULL SRID 0,
    generated_col INT GENERATED ALWAYS AS (int_col + 1) STORED,
    PRIMARY KEY (id_col),
    KEY idx_{table_name}_int (int_col),
    KEY idx_{table_name}_varchar (varchar_col)
) ENGINE=InnoDB;

INSERT INTO {table_name}
    (tinyint_col, smallint_col, mediumint_col, int_col, bigint_col, decimal_col,
     float_col, double_col, bit_col, char_col, varchar_col, binary_col,
     varbinary_col, text_col, longtext_col, blob_col, enum_col, set_col,
     date_col, time_col, datetime_col, timestamp_col, year_col, json_col,
     point_col)
VALUES
    (1, 2, 3, 4, 5, 6.2500, 1.5, 2.5, b'10101010', 'char-a', 'varchar-a',
     X'0102030405060708', X'0A0B0C', 'text-a', 'longtext-a', X'FFAA',
     'red', 'a,b', DATE '2020-01-01', TIME '12:00:00',
     TIMESTAMP '2020-01-01 12:00:00', TIMESTAMP '2020-01-01 12:00:00',
     2020, JSON_OBJECT('id', 1), ST_GeomFromText('POINT(1 1)', 0));
